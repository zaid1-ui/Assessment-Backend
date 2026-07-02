from marshmallow import Schema, fields, validate


class UserCreateSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))


class UserUpdateSchema(Schema):
    username = fields.String(validate=validate.Length(min=3, max=80))
    email = fields.Email()
