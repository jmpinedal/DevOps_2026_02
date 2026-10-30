# Blacklist Service

Microservicio REST para administrar una lista negra global de direcciones de correo electrónico. Los clientes pueden agregar direcciones bloqueadas y consultar si una dirección está en la lista, junto con el motivo registrado.

## Contenido

- [Características](#características)
- [Tecnologías](#tecnologías)
- [Requisitos](#requisitos)
- [Ejecución local](#ejecución-local)
- [API](#api)
- [Configuración](#configuración)
- [Pruebas](#pruebas)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Despliegue](#despliegue)

## Características

- Alta y consulta de direcciones de correo mediante una API REST.
- Autenticación JWT para los endpoints de la lista; el endpoint de salud es público.
- Normalización de emails a minúsculas para evitar duplicados por diferencias de mayúsculas.
- Validación del email, UUID de aplicación y longitud del motivo de bloqueo.
- Registro de la IP de origen y la fecha/hora UTC al crear una entrada.
- PostgreSQL como base de datos de ejecución y SQLite en memoria para las pruebas.

## Tecnologías

- Python 3.10 o superior
- Flask y Flask-RESTful
- Flask-SQLAlchemy y PostgreSQL
- Flask-JWT-Extended
- Marshmallow
- pytest

## Requisitos

- Python 3.10+
- Docker para iniciar PostgreSQL localmente, o una instancia de PostgreSQL accesible

## Ejecución local

Desde la raíz del repositorio, inicia una base de datos PostgreSQL de desarrollo:

```bash
docker run -d --name blacklist-pg -p 5432:5432 \
  -e POSTGRES_USER=blacklist \
  -e POSTGRES_PASSWORD=blacklist \
  -e POSTGRES_DB=blacklist \
  postgres:16-alpine
```

Instala las dependencias y configura el servicio:

```bash
cd blacklist-service
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

export FLASK_APP=wsgi.py
export JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export DATABASE_URL="postgresql+psycopg2://blacklist:blacklist@localhost:5432/blacklist"
```

Inicializa las tablas y ejecuta la aplicación:

```bash
.venv/bin/flask init-db
.venv/bin/flask run --host 0.0.0.0 --port 5000
```

La API queda disponible en `http://localhost:5000`. Para generar el JWT de desarrollo en otra terminal, vuelve a establecer las mismas variables de entorno (incluido el mismo `JWT_SECRET_KEY`) y ejecuta:

```bash
cd blacklist-service
export FLASK_APP=wsgi.py
export JWT_SECRET_KEY="<el mismo secreto configurado al iniciar la API>"
export DATABASE_URL="postgresql+psycopg2://blacklist:blacklist@localhost:5432/blacklist"
TOKEN=$(.venv/bin/flask create-token)
```

El comando `create-token` imprime un token sin expiración. Usa un secreto aleatorio, mantenlo privado y no reutilices el ejemplo de base de datos de desarrollo en producción.

## API

Todos los endpoints, excepto `GET /health`, requieren el encabezado:

```http
Authorization: Bearer <TOKEN>
```

### `POST /blacklists`

Agrega una dirección a la lista negra.

```bash
curl -X POST http://localhost:5000/blacklists \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "spam@example.com",
    "app_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "blocked_reason": "phishing"
  }'
```

| Campo | Requerido | Restricciones |
|---|---:|---|
| `email` | Sí | Dirección válida; máximo 254 caracteres |
| `app_uuid` | Sí | UUID válido de la aplicación cliente |
| `blocked_reason` | No | Texto de hasta 255 caracteres; admite `null` |

Respuestas habituales: `201` creada, `400` datos inválidos, `401` token ausente o inválido y `409` email ya registrado.

### `GET /blacklists/<email>`

Consulta una dirección. La búsqueda no distingue mayúsculas y minúsculas.

```bash
curl "http://localhost:5000/blacklists/spam%40example.com" \
  -H "Authorization: Bearer $TOKEN"
```

Respuesta cuando está en la lista:

```json
{
  "email": "spam@example.com",
  "is_blacklisted": true,
  "blocked_reason": "phishing"
}
```

Si no existe, responde `200` con `"is_blacklisted": false` y `"blocked_reason": null`.

### `GET /health`

Verificación pública del estado del servicio:

```bash
curl http://localhost:5000/health
```

```json
{"status": "ok"}
```

## Configuración

| Variable | Requerida | Descripción |
|---|---:|---|
| `JWT_SECRET_KEY` | Sí | Secreto para firmar y validar JWT. Usa un valor aleatorio fuerte (al menos 32 caracteres) y guárdalo como secreto de entorno. |
| `DATABASE_URL` | No | URL de conexión PostgreSQL. Si no se define, el servicio usa su configuración local predeterminada. |
| `TRUST_PROXY_HEADERS` | No | Por defecto `false`. Actívala solo cuando la aplicación esté detrás de un proxy de confianza que establece `X-Forwarded-For`. |

En Elastic Beanstalk, el servicio puede construir la conexión TLS a RDS usando las variables `RDS_*` proporcionadas por el entorno y el bundle de certificados incluido. La configuración de entorno activa `TRUST_PROXY_HEADERS`.

## Pruebas

Desde la carpeta `blacklist-service`:

```bash
.venv/bin/python -m pytest -q
```

La suite utiliza SQLite en memoria, por lo que no requiere PostgreSQL.

## Estructura del repositorio

```text
.
├── blacklist-service/
│   ├── app/              # Aplicación Flask, recursos, modelos y configuración
│   ├── tests/            # Pruebas automatizadas
│   ├── certs/            # Certificados CA para conexiones TLS a AWS RDS
│   ├── requirements.txt  # Dependencias Python
│   ├── wsgi.py           # Punto de entrada WSGI
│   └── README.md         # Guía detallada del microservicio
├── postman/              # Colección de solicitudes para Postman
└── LICENSE
```

También puedes importar la colección [Blacklist API - Entrega 1](./postman/Blacklist%20API%20-%20Entrega%201.postman_collection.json) en Postman. La documentación específica del servicio está en [blacklist-service/README.md](./blacklist-service/README.md).

## Despliegue

El servicio incluye un `Procfile` de Gunicorn y configuración para AWS Elastic Beanstalk en `blacklist-service/.ebextensions/`. Configura `JWT_SECRET_KEY` en el entorno de despliegue y proporciona una base PostgreSQL/RDS antes de publicar la aplicación.

test
---
