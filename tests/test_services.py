"""Smoke test — verifies the core pipeline can be imported and basic ops work."""

import cv2
import numpy as np


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
