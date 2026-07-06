from marshmallow import Schema, fields, validate


class ProjectCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    description = fields.String(required=False, allow_none=True)
    # owner_id intentionally removed: the owner is always the logged-in user.


class ProjectUpdateSchema(Schema):
    name = fields.String(validate=validate.Length(min=1, max=120))
    description = fields.String(allow_none=True)
