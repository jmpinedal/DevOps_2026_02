import os
from urllib.parse import quote_plus

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _database_url():
    # Elastic Beanstalk inyecta RDS_* al asociar una base RDS al entorno.
    if "RDS_HOSTNAME" in os.environ:
        # quote_plus: la contraseña puede contener caracteres como @, : o /.
        user = quote_plus(os.environ["RDS_USERNAME"])
        password = quote_plus(os.environ["RDS_PASSWORD"])
        # RDS fuerza TLS. verify-full valida el certificado y el nombre del host
        # contra el bundle oficial de AWS incluido en el proyecto (certs/).
        ca_bundle = os.path.join(BASE_DIR, "certs", "global-bundle.pem")
        return (
            f"postgresql+psycopg2://{user}:{password}"
            f"@{os.environ['RDS_HOSTNAME']}:{os.environ.get('RDS_PORT', '5432')}"
            f"/{os.environ['RDS_DB_NAME']}"
            f"?sslmode=verify-full&sslrootcert={quote_plus(ca_bundle)}&connect_timeout=5"
        )
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://blacklist:blacklist@localhost:5432/blacklist",
    )
    # Algunos PaaS (p. ej. Heroku) entregan URLs con el esquema "postgres://",
    # que SQLAlchemy 2.x ya no acepta.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


class Config:
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Sin valor por defecto: la aplicación no arranca sin un secreto explícito.
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    # Activar solo si la app está detrás de un proxy/balanceador de confianza,
    # de lo contrario cualquier cliente podría falsear la IP de origen.
    TRUST_PROXY_HEADERS = os.environ.get("TRUST_PROXY_HEADERS", "false").lower() == "true"


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    JWT_SECRET_KEY = "test-secret-with-at-least-32-bytes!!"
    TRUST_PROXY_HEADERS = False
