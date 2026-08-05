# Telegram bot

## 1. Registrar la aplicación en Telegram

### 1.1 Crear el bot con @BotFather

1. Abrí Telegram y buscá el bot oficial **@BotFather** (cuenta verificada).
2. Iniciá un chat y enviá `/newbot`.
3. BotFather te pide un **nombre** para mostrar (ej. `Mi Biblioteca`).
4. Luego un **username** único, que **debe terminar en `bot`** (ej. `mi_biblioteca_bot`).
5. Si el username está disponible, BotFather responde con:

   - El **token de acceso** (clave larga tipo `1234567890:AAH...`). Guardalo, solo se ve una vez.
   - Un link de acceso tipo `t.me/mi_biblioteca_bot`.

### 1.2 Configurar comandos (opcional pero recomendado)

Enviá a BotFather `/setcommands` y elegí tu bot. Pegá:

```
nuevo - Registrar un libro enviando fotos
listo - Procesar las fotos enviadas
cancel - Cancelar la operacion
```

### 1.3 Opcionales

- `/setdescription` — texto breve que se muestra al abrir el bot.
- `/setuserpic` — foto de perfil para el bot.

### 1.4 Verificar el token

El bot usa *polling*, solo necesita conexión saliente. Probá el token desde el servidor:

```bash
curl https://api.telegram.org/bot<TOKEN>/getMe
```

Debe responder con `"ok": true` y el nombre del bot.

---

## 2. Levantar la aplicación en un servidor casero

### 2.1 Requisitos

- Un servidor casero: PC vieja, Raspberry Pi o mini-PC con Linux.
- Docker + Docker Compose (Docker Engine v27+).
- git.
- Conexión a internet con salida HTTPS (no hace falta IP pública ni abrir puertos: el bot consulta a Telegram, no al revés).

### 2.2 Descargar el proyecto

```bash
git clone <url-del-repo> biblioteca
cd biblioteca
```

### 2.3 Crear las variables de entorno

Crear `.env` en la raíz del proyecto (no está versionado):

```bash
BIBLIOTECA_TELEGRAM_BOT_TOKEN=tu_token_de_botfather
```

Opcionales:

| Variable | Default | Uso |
|----------|---------|-----|
| `BIBLIOTECA_API_BASE_URL` | `http://127.0.0.1:8000` | URL de la API que usa el bot (en Docker: `http://api:8000`) |
| `BIBLIOTECA_DATABASE_URL` | `sqlite:///./biblioteca.db` | Ruta de la base de datos |
| `BIBLIOTECA_STORAGE_PATH` | `storage/images` | Carpeta de imágenes guardadas |

### 2.4 Construir y levantar

```bash
docker compose -f Dockers/desa/docker-compose.yml build
docker compose -f Dockers/desa/docker-compose.yml up -d
```

- La primera construcción tarda (instala OpenCV + PaddleOCR, que es pesado).
- Se levantan dos servicios: `api` (FastAPI en `localhost:8000`) y `bot` (Telegram).
- El bot se conecta a la API internamente vía `http://api:8000`.

### 2.5 Verificar que funciona

```bash
docker compose -f Dockers/desa/docker-compose.yml logs -f
```

Deberías ver el log `Bot started — polling`. Luego abrí Telegram y escribile a tu bot:

```
/nuevo
```

Enviá una foto de la contraportada del libro (con el código de barras) y terminá con `/listo`.

### 2.6 Seguridad

- **No expongas el puerto 8000 hacia internet**: el endpoint `/api/books/process-image` no tiene autenticación. Dejá que solo el bot (y tu red local) lo alcance. El bot usa *polling*, así que no necesitás abrir puertos de entrada.
- Protegé el token: solo vive en `.env`, no lo versiones ni lo compartas.

### 2.7 Reinicio automático

El compose de desarrollo no trae política de reinicio. Para que sobreviva a reinicios del servidor, agregá en `Dockers/desa/docker-compose.yml` en cada servicio:

```yaml
    restart: unless-stopped
```

Alternativa sin Docker: un servicio systemd (`/etc/systemd/system/biblioteca.service`) que ejecute los dos comandos del proyecto:

```ini
[Unit]
Description=Biblioteca bot
After=network-online.target

[Service]
WorkingDirectory=/ruta/a/biblioteca
EnvironmentFile=/ruta/a/biblioteca/.env
ExecStart=/usr/bin/uv run python -m app.bot
Restart=always

[Install]
WantedBy=multi-user.target
```

(El equivalente para la API usa `uv run uvicorn app.api:app --host 0.0.0.0 --port 8000`.)

### 2.8 Respaldo de datos

Los libros, la base SQLite y las imágenes se guardan en el volumen Docker `storage_data`, que persiste entre reinicios de contenedores pero **no** se elimina solo si borrás el proyecto. Para respaldar:

```bash
docker run --rm -v biblioteca_storage_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/storage_backup.tar.gz /data
```

## Notas

- **Polling, no webhook:** el bot le pregunta a Telegram en bucle. No requiere dominio, IP pública ni port-forwarding — ideal para servidor casero.
- **PaddleOCR:** la primera inferencia tarda ~10s (descarga modelos). Las siguientes son más rápidas.
- El bot responde por cada foto; enviar varias fotos y cerrar con `/listo` procesa todas. Cualquier cosa se cancela con `/cancel`.
