"""Integracion del endpoint process-image: pipeline completo con servicios mockeados."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import api as api_module
from app.database import Base, get_db
from app.models import Book


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    api_module.app.dependency_overrides[get_db] = override_get_db
    yield testing_session
    api_module.app.dependency_overrides.clear()


@pytest.fixture()
def client(db_session):
    return TestClient(api_module.app)


def test_process_image_with_isbn(client, db_session, monkeypatch, tmp_path):
    """ISBN detectado: Open Library completa titulo/autor/editorial y se persiste en DB."""
    monkeypatch.setattr(api_module, "save_image", lambda b: tmp_path / "fake.webp")
    monkeypatch.setattr(api_module, "read_barcode", lambda b: "9789500000000")

    async def fake_lookup(isbn):
        return {"title": "El Aleph", "author": "Jorge Luis Borges", "publisher": "Editorial Sur"}

    monkeypatch.setattr(api_module, "lookup_open_library", fake_lookup)
    monkeypatch.setattr(api_module, "ocr_text", lambda b: "")

    files = {"file": ("foto.jpg", b"data", "image/jpeg")}
    resp = client.post("/api/books/process-image", files=files)

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["book"]["title"] == "El Aleph"
    assert body["book"]["isbn"] == "9789500000000"
    assert body["book"]["image_path"] == str(tmp_path / "fake.webp")

    book = db_session().query(Book).one()
    assert book.title == "El Aleph"
    assert book.isbn == "9789500000000"


def test_process_image_ocr_fallback(client, db_session, monkeypatch, tmp_path):
    """Sin ISBN: el OCR provee titulo/autor y el ISBN se extrae del texto OCR."""
    fake_path = tmp_path / "fake.webp"
    fake_path.write_bytes(b"jpeg")
    monkeypatch.setattr(api_module, "save_image", lambda b: fake_path)
    monkeypatch.setattr(api_module, "read_barcode", lambda b: None)
    monkeypatch.setattr(api_module, "lookup_open_library", lambda isbn: None)
    text = "El Aleph\nJorge Luis Borges\nEditorial Sur\n9789500000000"
    monkeypatch.setattr(api_module, "ocr_text", lambda b: text)

    files = {"file": ("foto.jpg", b"data", "image/jpeg")}
    resp = client.post("/api/books/process-image", files=files)

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["book"]["title"] == "El Aleph"
    assert body["book"]["author"] == "Jorge Luis Borges"

    book = db_session().query(Book).one()
    assert book.title == "El Aleph"
    assert book.author == "Jorge Luis Borges"
    assert book.isbn == "9789500000000"


def test_process_image_rejects_invalid_image(client, db_session):
    """Una imagen no decodificable da 400 y no persiste nada."""
    files = {"file": ("basura.jpg", b"no soy una imagen", "image/jpeg")}
    resp = client.post("/api/books/process-image", files=files)

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Imagen no decodificable"
    assert db_session().query(Book).count() == 0


def test_list_books_empty(client):
    """Sin libros, el listado devuelve una lista vacia."""
    resp = client.get("/api/books")
    assert resp.status_code == 200
    assert resp.json() == {"books": []}


def test_list_books_returns_books_ordered_by_creation(client, db_session):
    """Lista los libros, del mas reciente al mas antiguo."""
    from datetime import datetime, timedelta

    now = datetime(2024, 1, 1, 12, 0, 0)
    older = Book(title="Viejo", isbn="1", image_path="/a", created_at=now - timedelta(days=1))
    newer = Book(title="Nuevo", isbn="2", image_path="/b", created_at=now)
    db = db_session()
    db.add(older)
    db.add(newer)
    db.commit()

    resp = client.get("/api/books")
    assert resp.status_code == 200
    body = resp.json()
    assert [b["title"] for b in body["books"]] == ["Nuevo", "Viejo"]


def test_get_book_by_id(client, db_session):
    """Devuelve el libro con el id indicado."""
    book = Book(title="El Aleph", isbn="9789500000000", image_path="/a")
    db = db_session()
    db.add(book)
    db.commit()
    db.refresh(book)

    resp = client.get(f"/api/books/{book.id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == book.id
    assert body["title"] == "El Aleph"
    assert body["isbn"] == "9789500000000"


def test_get_book_not_found(client):
    """Id inexistente devuelve 404."""
    resp = client.get("/api/books/no-such-id")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Libro no encontrado"