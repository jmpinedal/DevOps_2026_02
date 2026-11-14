# Imagen del microservicio Blacklist para AWS Fargate
FROM public.ecr.aws/docker/library/python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=application.py

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codigo, incluido certs/global-bundle.pem (TLS hacia RDS)
COPY . .

EXPOSE 8000

# Crea las tablas si no existen y arranca gunicorn (antes lo hacia .ebextensions)
CMD ["sh", "-c", "flask init-db && exec gunicorn --bind 0.0.0.0:8000 --workers 2 --access-logfile - application:application"]
