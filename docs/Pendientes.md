## Pendientes

### Infraestructura
- [x] Dockerfile + docker-compose.yml con volumes (imagen dev, live reload)
- [x] Docs de despliegue casero + registro del bot (docs/Telegram bot.md)
- [ ] Agregar `restart: unless-stopped` al docker-compose para que sobreviva reinicios del servidor (hoy se hace a mano)
- [ ] Automatizar backups del volumen `storage_data` (cron/script) — hoy el respaldo es manual
- [ ] Dockerfile multi-stage para producción (imagen optimizada, sin volúmenes de código)
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
- [ ] Endpoint GET `/api/books/report.pdf` — reporte PDF de libros con **ReportLab** (`platypus.SimpleDocTemplate` + `Table`), sobre el listado de libros

### Bot
- [ ] Comando `/listar` para ver libros registrados
- [ ] Comando `/buscar <término>` para búsqueda por título/autor/ISBN
- [ ] Botones inline para confirmar o descartar antes de persistir
- [ ] Soporte para envío de múltiples fotos en un solo mensaje (no solo una por vez)

### Testing
- [x] Tests de integración para el endpoint (TestClient de FastAPI)
- [ ] Test del pipeline completo con imagen real de libro
- [x] Mock de Open Library para tests offline
- [x] Tests de los handlers del bot con fakes (sin Telegram real)
- [ ] Test de `_decode_barcodes` con imagen real de código de barras (ISBN-13)
