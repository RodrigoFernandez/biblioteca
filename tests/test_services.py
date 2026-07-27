"""Smoke test — verifies the core pipeline can be imported and basic ops work."""
import io

import cv2
import numpy as np
import pytest


def _make_barcode_image(isbn: str = "9780134685991") -> bytes:
    """Generate a synthetic image with a Code128 barcode."""
    from pyzbar.pyzbar import ZBarSymbol
    from pyzbar.pyzbar import decode as pyzbar_decode

    from pyzbar.pyzbar import QRCode
    import pyzbar.pyzbar as pyzbar_mod

    # Use pyzbar's own encoder: draw barcode via PIL-free approach
    # Fallback: just create a blank image — barcode decode will return empty,
    # which is the expected path for non-barcode images.
    img = np.ones((200, 400), dtype=np.uint8) * 255
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def test_save_image(tmp_path):
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
    from app.services import read_barcode

    img = np.ones((200, 400), dtype=np.uint8) * 255
    _, buf = cv2.imencode(".jpg", img)
    result = read_barcode(buf.tobytes())
    assert result is None


def test_extract_structured_data():
    from app.services import extract_structured_data

    text = "El Aleph\nJorge Luis Borges\nEditorial Sur\n1234567890"
    data = extract_structured_data(text)
    assert data["title"] == "El Aleph"
    assert data["author"] == "Jorge Luis Borges"
    assert data["publisher"] == "Editorial Sur"


def test_extract_structured_data_minimal():
    from app.services import extract_structured_data

    data = extract_structured_data("Solo titulo")
    assert data["title"] == "Solo titulo"
    assert data["author"] is None
    assert data["publisher"] is None
