import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.models import Book
from app.schemas import BookResponse, ImageProcessResponse, ListBooksResponse
from app.services import (
    extract_isbn,
    extract_structured_data,
    lookup_open_library,
    ocr_text,
    read_barcode,
    save_image,
)

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Al arrancar: crea las tablas en la BD y asegura que exista el directorio de storage."""
    Base.metadata.create_all(bind=engine)
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Biblioteca API", lifespan=lifespan)


@app.get("/api/books", response_model=ListBooksResponse)
def list_books(db: Session = Depends(get_db)) -> ListBooksResponse:
    """Lista los libros subidos, del mas reciente al mas antiguo."""
    books = db.query(Book).order_by(Book.created_at.desc()).all()
    return ListBooksResponse(books=[BookResponse.model_validate(b) for b in books])


@app.get("/api/books/{book_id}", response_model=BookResponse)
def get_book(book_id: str, db: Session = Depends(get_db)) -> BookResponse:
    """Devuelve un libro puntual por su id."""
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return BookResponse.model_validate(book)


@app.post("/api/books/process-image", response_model=ImageProcessResponse)
async def process_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImageProcessResponse:
    """Procesa una imagen: guarda, lee el codigo de barras, consulta Open Library,
    usa OCR como fallback y registra el libro en la BD."""
    image_bytes = await file.read()

    image_path = save_image(image_bytes)

    book_data: dict[str, str | None] = {
        "title": None,
        "author": None,
        "publisher": None,
        "isbn": None,
    }

    isbn = read_barcode(image_bytes)
    book_data["isbn"] = isbn

    if isbn:
        log.info("ISBN detected: %s — querying Open Library", isbn)
        lookup = await lookup_open_library(isbn)
        if lookup:
            book_data.update(lookup)

    if not book_data["title"]:
        raw_text = ocr_text(image_bytes)
        if raw_text:
            log.info("OCR fallback — extracting structured data")
            book_data.update(extract_structured_data(raw_text))
            if not book_data["isbn"]:
                book_data["isbn"] = extract_isbn(raw_text)

    book = Book(
        title=book_data["title"],
        author=book_data["author"],
        publisher=book_data["publisher"],
        isbn=book_data["isbn"],
        image_path=str(image_path),
    )
    db.add(book)
    db.commit()
    db.refresh(book)

    return ImageProcessResponse(
        success=True,
        book=BookResponse.model_validate(book),
        message="Libro registrado exitosamente",
    )


def main() -> None:
    """Levanta la API con Uvicorn en 0.0.0.0:8000."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
