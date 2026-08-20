"""Tests con fotos reales de libros. Requieren el extra [ocr] (paddleocr)."""

from pathlib import Path

import pytest

from app.config import settings
from tests.test_api import client, db_session  # noqa: F401

pytest.importorskip("paddleocr")

FIXTURES = Path(__file__).parent / "fixtures"
EXPECTED_ISBN = {
    "matematica_discreta": "9504200214",
    "miguel_angel": "8434581477",
}


@pytest.mark.parametrize(("book", "isbn"), EXPECTED_ISBN.items())
def test_process_book_folder_real_photos(client, db_session, monkeypatch, tmp_path, book, isbn):  # noqa: F811
    """Procesa las fotos de un libro y verifica que al menos una produzca su ISBN."""
    folder = FIXTURES / book
    photos = sorted(folder.glob("*")) if folder.is_dir() else []
    if not photos:
        pytest.skip(f"no hay fotos en {folder}")

    monkeypatch.setattr(settings, "storage_path", tmp_path)

    isbn_found = False
    title_found = False
    for photo in photos:
        resp = client.post(
            "/api/books/process-image",
            files={"file": (photo.name, photo.read_bytes(), "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()["book"]
        isbn_found = isbn_found or body["isbn"] == isbn
        title_found = title_found or bool(body["title"])

    assert isbn_found, f"ninguna foto de {book} produjo el ISBN {isbn}"
    assert title_found, f"ninguna foto de {book} produjo un titulo"