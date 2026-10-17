from datetime import datetime, timezone

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import BlacklistEntry
from app.schemas import BlacklistCreateSchema, BlacklistStatusSchema

create_schema = BlacklistCreateSchema()
status_schema = BlacklistStatusSchema()


def _normalize_email(email):
    # Se guarda en minúsculas para que "Juan@Mail.com" y "juan@mail.com"
    # no permitan evadir la lista negra.
    return email.strip().lower()


def _client_ip():
    # Con TRUST_PROXY_HEADERS activo, ProxyFix ya reemplaza remote_addr por la
    # IP original reportada por el proxy de confianza.
    return request.remote_addr or "unknown"


class BlacklistResource(Resource):
    method_decorators = [jwt_required()]

    def post(self):
        payload = request.get_json(silent=True)
        if payload is None:
            return {"message": "El cuerpo de la solicitud debe ser JSON válido"}, 400

        try:
            data = create_schema.load(payload)
        except ValidationError as err:
            return {"message": err.messages}, 400

        email = _normalize_email(data["email"])
        entry = BlacklistEntry(
            email=email,
            app_uuid=str(data["app_uuid"]),
            blocked_reason=data["blocked_reason"],
            ip_address=_client_ip(),
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(entry)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"message": f"El email {email} ya se encuentra en la lista negra"}, 409

        return {"message": f"El email {email} fue agregado a la lista negra"}, 201


class BlacklistEmailResource(Resource):
    method_decorators = [jwt_required()]

    def get(self, email):
        normalized = _normalize_email(email)
        entry = db.session.scalar(db.select(BlacklistEntry).filter_by(email=normalized))
        result = {
            "email": normalized,
            "is_blacklisted": entry is not None,
            "blocked_reason": entry.blocked_reason if entry else None,
        }
        return status_schema.dump(result), 200
