"""Tests de los handlers del bot con fakes minimos (sin red ni Telegram real)."""

import asyncio

from telegram.ext import ConversationHandler

from app import bot as bot_module


class FakeFile:
    def __init__(self, data: bytes):
        self._data = data

    async def download_as_bytearray(self):
        return bytearray(self._data)


class FakeBot:
    def __init__(self, files: dict[str, bytes]):
        self.files = {fid: FakeFile(data) for fid, data in files.items()}

    async def get_file(self, file_id: str):
        return self.files[file_id]


class FakePhoto:
    def __init__(self, file_id: str):
        self.file_id = file_id


class FakeMessage:
    def __init__(self, photos: list[str] | None = None):
        self.replies: list[str] = []
        self.photo = [FakePhoto(fid) for fid in (photos or [])]

    async def reply_text(self, text: str):
        self.replies.append(text)


class FakeUpdate:
    def __init__(self, message: FakeMessage):
        self.message = message


class FakeContext:
    def __init__(self, bot: FakeBot):
        self.bot = bot
        self.user_data: dict = {}


class FakeResponse:
    def __init__(self, data: dict):
        self._data = data

    def json(self) -> dict:
        return self._data


class FakeAsyncClient:
    def __init__(self, responses: list[FakeResponse]):
        self._responses = responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, *args, **kwargs):
        return self._responses.pop(0)


def _run(coro):
    return asyncio.run(coro)


def test_start_nuevo():
    msg = FakeMessage()
    update, ctx = FakeUpdate(msg), FakeContext(FakeBot({}))

    state = _run(bot_module.start_nuevo(update, ctx))

    assert state == bot_module.WAITING_PHOTO
    assert ctx.user_data["photos"] == []
    assert "Envia una o mas fotos" in msg.replies[0]


def test_receive_photo():
    bot = FakeBot({"fid1": b"img1", "fid2": b"img2"})
    msg = FakeMessage(photos=["fid1", "fid2"])
    update, ctx = FakeUpdate(msg), FakeContext(bot)
    ctx.user_data["photos"] = []

    state = _run(bot_module.receive_photo(update, ctx))

    assert state == bot_module.WAITING_PHOTO
    assert ctx.user_data["photos"] == [b"img2"]
    assert msg.replies[-1] == "Foto recibida (1). Puedes enviar otra o /listo para procesar."


def test_process_photos_success(monkeypatch):
    book = {
        "title": "El Aleph",
        "author": "Jorge Luis Borges",
        "publisher": "Editorial Sur",
        "isbn": "9789500000000",
    }
    client = FakeAsyncClient(
        [
            FakeResponse({"success": True, "book": book}),
            FakeResponse({"success": True, "book": {**book, "title": None}}),
        ]
    )
    monkeypatch.setattr(bot_module.httpx, "AsyncClient", lambda **k: client)

    msg = FakeMessage()
    update, ctx = FakeUpdate(msg), FakeContext(FakeBot({}))
    ctx.user_data["photos"] = [b"a", b"b"]

    state = _run(bot_module.process_photos(update, ctx))

    assert state == ConversationHandler.END
    assert msg.replies[0] == "Procesando 2 foto(s)..."
    assert "Titulo: El Aleph" in msg.replies[1]
    assert "ISBN: 9789500000000" in msg.replies[1]
    assert "Titulo: No detectado" in msg.replies[2]


def test_process_photos_api_error(monkeypatch):
    resp = FakeResponse({"success": False, "book": None, "message": "OCR fallo"})
    client = FakeAsyncClient([resp])
    monkeypatch.setattr(bot_module.httpx, "AsyncClient", lambda **k: client)

    msg = FakeMessage()
    update, ctx = FakeUpdate(msg), FakeContext(FakeBot({}))
    ctx.user_data["photos"] = [b"a"]

    state = _run(bot_module.process_photos(update, ctx))

    assert state == ConversationHandler.END
    assert msg.replies[-1] == "Error: OCR fallo"


def test_process_photos_sin_fotos():
    msg = FakeMessage()
    update, ctx = FakeUpdate(msg), FakeContext(FakeBot({}))

    state = _run(bot_module.process_photos(update, ctx))

    assert state == ConversationHandler.END
    assert msg.replies[0] == "No enviaste ninguna foto. Usa /nuevo para empezar."