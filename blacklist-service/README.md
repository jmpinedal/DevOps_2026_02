# Blacklist Service

Microservicio REST para gestionar la lista negra global de emails de la organización.
Stack: Python, Flask, Flask-SQLAlchemy, Flask-RESTful, Flask-Marshmallow, Flask-JWT-Extended, Werkzeug y PostgreSQL.

## Endpoints

Todas las rutas requieren `Authorization: Bearer <token>`.

### `POST /blacklists`

Agrega un email a la lista negra global.

```json
{
  "email": "spam@example.com",
  "app_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "blocked_reason": "phishing"
}
```

- `email` (obligatorio): email válido, máximo 254 caracteres.
- `app_uuid` (obligatorio): UUID de la aplicación cliente.
- `blocked_reason` (opcional): motivo, máximo 255 caracteres.

Respuestas:

| Código | Significado |
|--------|-------------|
| 201 | Email agregado. `{"message": "..."}` |
| 400 | Datos inválidos. `{"message": {campo: [errores]}}` |
| 401 | Token ausente o inválido. |
| 409 | El email ya estaba en la lista negra. |

La IP de origen y la fecha/hora de la solicitud se guardan automáticamente.

### `GET /blacklists/<email>`

Indica si el email está en la lista negra y el motivo.

```json
{
  "email": "spam@example.com",
  "is_blacklisted": true,
  "blocked_reason": "phishing"
}
```

Si el email no está, responde 200 con `is_blacklisted: false` y `blocked_reason: null`.

### `GET /health`

Verificación de estado para el PaaS. No requiere token.

## Reglas de negocio

- Los emails se guardan y consultan en minúsculas, para que `Juan@Mail.com` y `juan@mail.com` sean el mismo registro.
- Cada email aparece una sola vez en la lista negra (restricción `UNIQUE`).

## Configuración

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `JWT_SECRET_KEY` | Sí | Secreto para firmar los tokens. Usar al menos 32 caracteres aleatorios. |
| `DATABASE_URL` | No | URL de PostgreSQL. Por defecto `postgresql+psycopg2://blacklist:blacklist@localhost:5432/blacklist`. |
| `TRUST_PROXY_HEADERS` | No | `true` solo si la app está detrás de un proxy de confianza que añade `X-Forwarded-For`. Por defecto `false`. |

## Ejecución local

```bash
cd blacklist-service
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

export FLASK_APP=wsgi.py
export JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export DATABASE_URL=postgresql+psycopg2://blacklist:blacklist@localhost:5432/blacklist

.venv/bin/flask init-db          # crea las tablas
.venv/bin/flask run --port 5000
```

Un PostgreSQL local rápido con Docker:

```bash
docker run -d --name blacklist-pg -p 5432:5432 \
  -e POSTGRES_USER=blacklist -e POSTGRES_PASSWORD=blacklist -e POSTGRES_DB=blacklist \
  postgres:16-alpine
```

### Token estático

El token no expira y se genera a partir de `JWT_SECRET_KEY`:

```bash
TOKEN=$(.venv/bin/flask create-token)
curl -X POST localhost:5000/blacklists \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"email":"spam@example.com","app_uuid":"3fa85f64-5717-4562-b3fc-2c963f66afa6","blocked_reason":"phishing"}'
```

## Pruebas

```bash
.venv/bin/python -m pytest -q
```

Las pruebas usan SQLite en memoria, así que no necesitan PostgreSQL.
