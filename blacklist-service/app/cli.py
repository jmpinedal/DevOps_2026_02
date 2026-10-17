import click
from flask_jwt_extended import create_access_token

from app.extensions import db


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Crea las tablas de la lista negra si no existen."""
        db.create_all()
        click.echo("Base de datos inicializada.")

    @app.cli.command("create-token")
    @click.option("--identity", default="blacklist-client", show_default=True)
    def create_token(identity):
        """Imprime el token estático (sin expiración) para autorizar las peticiones."""
        # expires_delta=False: el token es estático y predefinido, como permite el enunciado.
        click.echo(create_access_token(identity=identity, expires_delta=False))
