from __future__ import annotations

import uuid
from pathlib import Path

import cv2
import httpx
import numpy as np
from pyzbar.pyzbar import decode as pyzbar_decode

from app.config import settings


def save_image(file_bytes: bytes, suffix: str = ".jpg") -> Path:
    filename = f"{uuid.uuid4()}{suffix}"
    path = settings.storage_path / filename
    path.write_bytes(file_bytes)
    return path


def read_barcode(image_bytes: bytes) -> str | None:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None

    candidates = _decode_barcodes(img)
    if not candidates:
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        candidates = _decode_barcodes(thresh)

    return candidates[0] if candidates else None


def _decode_barcodes(img: np.ndarray) -> list[str]:
    results = pyzbar_decode(img)
    return [
        r.data.decode("utf-8")
        for r in results
        if r.data.decode("utf-8").replace("-", "").isdigit()
        and len(r.data.decode("utf-8").replace("-", "")) in (10, 13)
    ]


def ocr_text(image_bytes: bytes) -> str:
    """Lazy import PaddleOCR — only loads when called."""
    from paddleocr import PaddleOCR  # ponytail: heavy lib, lazy load

    ocr = PaddleOCR(use_angle_cls=True, lang="es", use_gpu=False, show_log=False)

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return ""

    result = ocr.ocr(img, cls=True)
    if not result or not result[0]:
        return ""

    return "\n".join(line[1][0] for line in result[0])


async def lookup_open_library(isbn: str) -> dict[str, str | None] | None:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"https://openlibrary.org/isbn/{isbn}.json")
        if resp.status_code != 200:
            return None
        data = resp.json()

    title = data.get("title")
    publishers = ", ".join(data["publishers"][:3]) if data.get("publishers") else None

    authors = None
    if data.get("authors"):
        names: list[str] = []
        for a in data["authors"][:3]:
            key = a.get("key", "")
            async with httpx.AsyncClient(timeout=10) as client:
                aresp = await client.get(f"https://openlibrary.org{key}.json")
                if aresp.status_code == 200:
                    names.append(aresp.json().get("name", ""))
        authors = ", ".join(n for n in names if n) or None

    return {"title": title, "author": authors, "publisher": publishers}


def extract_structured_data(raw_text: str) -> dict[str, str | None]:
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    text_lines = [line for line in lines if not line.replace(" ", "").isdigit()]

    result: dict[str, str | None] = {"title": None, "author": None, "publisher": None}
    if len(text_lines) >= 1:
        result["title"] = text_lines[0]
    if len(text_lines) >= 2:
        result["author"] = text_lines[1]
    if len(text_lines) >= 3:
        result["publisher"] = text_lines[2]
    return result
