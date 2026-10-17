from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from app.api import JWTAwareApi
from app.cli import register_cli
from app.config import Config
from app.extensions import db, jwt, ma
from app.resources import BlacklistEmailResource, BlacklistResource


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    if not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError("La variable de entorno JWT_SECRET_KEY es obligatoria")

    if app.config.get("TRUST_PROXY_HEADERS"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)

    api = JWTAwareApi(app)
    api.add_resource(BlacklistResource, "/blacklists")
    api.add_resource(BlacklistEmailResource, "/blacklists/<string:email>")

    @jwt.invalid_token_loader
    def _invalid_token(reason):
        return jsonify(message=reason), 401

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    register_cli(app)
    return app
