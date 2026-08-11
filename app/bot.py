from __future__ import annotations

import logging

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import settings

log = logging.getLogger(__name__)

WAITING_PHOTO = 1


async def start_nuevo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entrada del flujo /nuevo: resetea las fotos acumuladas y pide las imagenes."""
    await update.message.reply_text(  # type: ignore[union-attr]
        "Envia una o mas fotos del libro (portada y/o contraportada con codigo de barras).\n"
        "Cuando termines, envia /listo."
    )
    context.user_data["photos"] = []
    return WAITING_PHOTO


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Descarga la foto de mayor resolucion, la guarda en user_data y confirma el conteo."""
    photo = update.message.photo[-1]  # type: ignore[union-attr] — highest resolution
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    context.user_data["photos"].append(bytes(image_bytes))
    count = len(context.user_data["photos"])
    await update.message.reply_text(  # type: ignore[union-attr]
        f"Foto recibida ({count}). Puedes enviar otra o /listo para procesar."
    )
    return WAITING_PHOTO


async def process_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Envia cada foto a la API de procesamiento y reporta el resultado de cada una."""
    photos: list[bytes] = context.user_data.get("photos", [])
    if not photos:
        await update.message.reply_text(  # type: ignore[union-attr]
            "No enviaste ninguna foto. Usa /nuevo para empezar."
        )
        return ConversationHandler.END

    await update.message.reply_text(  # type: ignore[union-attr]
        f"Procesando {len(photos)} foto(s)..."
    )

    async with httpx.AsyncClient(timeout=30) as client:
        for i, photo_bytes in enumerate(photos):
            resp = await client.post(
                f"{settings.api_base_url}/api/books/process-image",
                files={"file": (f"photo_{i}.jpg", photo_bytes, "image/jpeg")},
            )
            data = resp.json()

            if data.get("success") and data.get("book"):
                book = data["book"]
                msg = (
                    f"Libro registrado:\n"
                    f"Titulo: {book.get('title') or 'No detectado'}\n"
                    f"Autor: {book.get('author') or 'No detectado'}\n"
                    f"Editorial: {book.get('publisher') or 'No detectada'}\n"
                    f"ISBN: {book.get('isbn') or 'No detectado'}"
                )
            else:
                msg = f"Error: {data.get('message', 'Error desconocido')}"

            await update.message.reply_text(msg)  # type: ignore[union-attr]

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Fallback /cancel: finaliza la conversacion sin procesar nada."""
    await update.message.reply_text("Operacion cancelada.")  # type: ignore[union-attr]
    return ConversationHandler.END


def main() -> None:
    """Arma la aplicacion con el ConversationHandler (/nuevo -> fotos -> /listo) y el polling."""
    application = Application.builder().token(settings.telegram_bot_token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("nuevo", start_nuevo)],
        states={
            WAITING_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                CommandHandler("listo", process_photos),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv)
    log.info("Bot started — polling")
    application.run_polling()


if __name__ == "__main__":
    main()
