## Pendientes

### Infraestructura
- [ ] Crear Dockerfile multi-stage (API + bot como servicios separados)
- [ ] docker-compose.yml con volumes para `storage/` y SQLite
- [ ] CI/CD: GitHub Actions con ruff + pytest

### Seguridad
- [ ] Autenticación en el endpoint `/api/books/process-image` (API key o JWT)
- [ ] Rate limiting en la API

### OCR
- [ ] Pre-warming de PaddleOCR en background thread al startup de la API (evitar latencia en primera llamada)
- [ ] Mejorar heurística `extract_structured_data` — detectar patrones de editorial, año, ISBN en texto OCR
- [ ] Soporte para múltiples idiomas en OCR (configurable)

### API
- [ ] Endpoint GET `/api/books` para listar libros registrados
- [ ] Endpoint GET `/api/books/{id}` para detalle
- [ ] Endpoint DELETE `/api/books/{id}`
- [ ] Paginación en listado

### Bot
- [ ] Comando `/listar` para ver libros registrados
- [ ] Comando `/buscar <término>` para búsqueda por título/autor/ISBN
- [ ] Botones inline para confirmar o descartar antes de persistir
- [ ] Soporte para envío de múltiples fotos en un solo mensaje (no solo una por vez)

### Testing
- [ ] Tests de integración para el endpoint (TestClient de FastAPI)
- [ ] Test del pipeline completo con imagen real de libro
- [ ] Mock de Open Library para tests offline
