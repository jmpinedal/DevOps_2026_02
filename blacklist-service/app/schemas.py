from marshmallow import EXCLUDE, fields, validate

from app.extensions import ma


class BlacklistCreateSchema(ma.Schema):
    class Meta:
        unknown = EXCLUDE

    email = fields.Email(required=True, validate=validate.Length(max=254))
    app_uuid = fields.UUID(required=True)
    blocked_reason = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=255),
    )


class BlacklistStatusSchema(ma.Schema):
    email = fields.String(required=True)
    is_blacklisted = fields.Boolean(required=True)
    blocked_reason = fields.String(required=True, allow_none=True)
