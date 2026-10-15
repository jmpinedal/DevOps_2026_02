from flask_jwt_extended.exceptions import JWTExtendedException
from flask_restful import Api
from jwt import PyJWTError


class JWTAwareApi(Api):
    """Api de Flask-RESTful que responde 401 a los errores de autenticación JWT.

    Flask-RESTful captura las excepciones de los recursos antes que los manejadores
    de Flask, así que sin esto un token ausente o inválido produce un 500.
    Los tokens que no se pueden decodificar llegan como PyJWTError sin envolver.
    """

    def handle_error(self, e):
        if isinstance(e, (JWTExtendedException, PyJWTError)):
            return self.make_response({"message": str(e)}, 401)
        return super().handle_error(e)
