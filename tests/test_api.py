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
    """Sin ISBN: el OCR provee titulo/autor y se persisten con isbn None."""
    monkeypatch.setattr(api_module, "save_image", lambda b: tmp_path / "fake.webp")
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
    assert book.isbn is None