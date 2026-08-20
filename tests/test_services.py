"""Smoke test — verifies the core pipeline can be imported and basic ops work."""

from pathlib import Path

import cv2
import httpx
import numpy as np
import pytest


def test_save_image(tmp_path):
    """Verifica que save_image guarda el archivo en storage_path y conserva los bytes."""
    from app.config import settings
    from app.services import save_image

    original = settings.storage_path
    settings.storage_path = tmp_path

    data = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    path = save_image(data)
    assert path.exists()
    assert path.read_bytes() == data

    settings.storage_path = original


def test_save_image_resizes_and_compresses_real_photos(tmp_path):
    """Verifica la promesa de storage: max 600px por lado y WebP mucho mas liviano."""
    from app.config import settings
    from app.services import save_image

    photos = sorted(Path(__file__).parent.glob("fixtures/*/*.jpg"))
    if not photos:
        pytest.skip("no hay fotos de prueba en tests/fixtures")

    original = settings.storage_path
    settings.storage_path = tmp_path
    try:
        for photo in photos:
            raw = photo.read_bytes()
            out = save_image(raw)
            img = cv2.imdecode(np.frombuffer(out.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
            h, w = img.shape[:2]
            assert max(h, w) <= 600, f"{photo.name}: {max(h, w)}px"
            assert out.suffix == ".webp"
            assert out.stat().st_size < len(raw) // 10, f"{photo.name} no comprimio"
    finally:
        settings.storage_path = original


def test_read_barcode_returns_none_on_blank():
    """Una imagen en blanco no tiene codigo de barras: read_barcode devuelve None."""
    from app.services import read_barcode

    img = np.ones((200, 400), dtype=np.uint8) * 255
    _, buf = cv2.imencode(".jpg", img)
    result = read_barcode(buf.tobytes())
    assert result is None


def test_extract_structured_data():
    """Texto completo: las 3 primeras lineas se mapean a titulo, autor y editorial."""
    from app.services import extract_structured_data

    text = "El Aleph\nJorge Luis Borges\nEditorial Sur\n1234567890"
    data = extract_structured_data(text)
    assert data["title"] == "El Aleph"
    assert data["author"] == "Jorge Luis Borges"
    assert data["publisher"] == "Editorial Sur"


def test_extract_structured_data_minimal():
    """Una sola linea: solo se completa el titulo, autor y editorial quedan en None."""
    from app.services import extract_structured_data

    data = extract_structured_data("Solo titulo")
    assert data["title"] == "Solo titulo"
    assert data["author"] is None
    assert data["publisher"] is None


def test_extract_structured_data_skips_numeric_lines():
    """El ISBN numerico (primera linea) no se toma como titulo: debe saltarse."""
    from app.services import extract_structured_data

    text = "9789500000000\nEl Aleph\nJorge Luis Borges\nEditorial Sur"
    data = extract_structured_data(text)
    assert data["title"] == "El Aleph"
    assert data["author"] == "Jorge Luis Borges"
    assert data["publisher"] == "Editorial Sur"


def test_extract_isbn():
    """Extrae ISBN-13 o ISBN-10 admitiendo espacios y guiones; None si no hay."""
    from app.services import extract_isbn

    assert extract_isbn("El Aleph\nISBN 978-950-420021-3\nEditorial Sur") == "9789504200213"
    assert extract_isbn("ISBN 950 42 0021 4") == "9504200214"
    assert extract_isbn("Matematica Discreta") is None


def test_lookup_open_library(monkeypatch):
    """Agrupa editoriales/autores (max 3) y devuelve None si no hay respuesta 200."""
    import app.services as services

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/isbn/"):
            return httpx.Response(
                200,
                json={
                    "title": "El Aleph",
                    "publishers": ["E1", "E2", "E3", "E4"],
                    "authors": [{"key": "/authors/OL1"}, {"key": "/authors/OL2"}],
                },
            )
        return httpx.Response(200, json={"name": f"Autor {request.url.path}"})

    def make_client(**kwargs):
        return real_client(transport=httpx.MockTransport(handler))

    real_client = httpx.AsyncClient
    monkeypatch.setattr(services.httpx, "AsyncClient", make_client)

    data = asyncio_run(services.lookup_open_library("9789500000000"))
    expected = {
        "title": "El Aleph",
        "author": "Autor /authors/OL1.json, Autor /authors/OL2.json",
        "publisher": "E1, E2, E3",
    }
    assert data == expected

    not_found = real_client(transport=httpx.MockTransport(lambda r: httpx.Response(404)))
    monkeypatch.setattr(services.httpx, "AsyncClient", lambda **kwargs: not_found)
    assert asyncio_run(services.lookup_open_library("9789500000000")) is None


def asyncio_run(coro):
    import asyncio

    return asyncio.run(coro)
