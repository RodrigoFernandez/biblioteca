## Pendientes

### Infraestructura
- [x] Dockerfile + docker-compose.yml con volumes (imagen dev, live reload)
- [x] Docs de despliegue casero + registro del bot (docs/Telegram bot.md)
- [x] Flujo Podman para desarrollo: script `scripts/pc` (wrapper `source .env` + `podman compose`), plugin `docker-compose-v2`, socket de Podman, `.env` único en la raíz, `.dockerignore` que excluye el `.env` del build context
- [ ] Agregar `restart: unless-stopped` al docker-compose para que sobreviva reinicios del servidor (hoy se hace a mano)
- [ ] Automatizar backups del volumen `storage_data` y del dir `data/` (SQLite en host) (cron/script) — hoy el respaldo es manual
- [ ] Dockerfile multi-stage para producción (imagen optimizada, sin volúmenes de código)
- [ ] Configurar logging dedicado de la app (niveles, formato, salida a archivo/rotación para api y bot)
- [ ] CI/CD: GitHub Actions con ruff + pytest

### Seguridad
- [x] Excluir el `.env` del build context (`.dockerignore` en la raíz) para que el token no entre en la imagen
- [ ] Autenticación en el endpoint `/api/books/process-image` (API key o JWT)
- [ ] Rate limiting en la API

### OCR
- [ ] Pre-warming de PaddleOCR en background thread al startup de la API (evitar latencia en primera llamada)
- [x] Extraer ISBN del texto OCR (`extract_isbn`) — ISBN-10/ISBN-13 con espacios/guiones
- [ ] Revisitar `enable_mkldnn=False` en `ocr_text()` y re-habilitarlo al subir paddlepaddle (bug PIR/oneDNN en 3.3.x CPU, `NotImplementedError`)
- [ ] Mejorar heurística `extract_structured_data` — detectar patrones de editorial, año
- [ ] Soporte para múltiples idiomas en OCR (configurable)

### API
- [x] Endpoint GET `/api/books` para listar libros registrados
- [x] Endpoint GET `/api/books/{id}` para detalle
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
- [x] Test del pipeline completo con imagen real de libro (`tests/test_fixtures.py`, requiere `[ocr]`)
- [x] Mock de Open Library para tests offline
- [x] Tests de los handlers del bot con fakes (sin Telegram real)
- [ ] Test de `_decode_barcodes` con imagen real de código de barras (ISBN-13)
- [ ] Reconciliar `EXPECTED_ISBN` de `miguel_angel`: 8434581477 no aparece en las fotos — el OCR del colofón detecta 8434581450
