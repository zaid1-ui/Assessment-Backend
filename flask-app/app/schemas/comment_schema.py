from marshmallow import Schema, fields, validate


class CommentCreateSchema(Schema):
    content = fields.String(required=True, validate=validate.Length(min=1))
    task_id = fields.Integer(required=True)
    # author_id intentionally removed: the author is always the logged-in user.
