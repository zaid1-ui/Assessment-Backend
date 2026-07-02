from marshmallow import Schema, fields, validate
from app.models.task import VALID_STATUSES, VALID_PRIORITIES


class TaskCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    description = fields.String(required=False, allow_none=True)
    status = fields.String(validate=validate.OneOf(VALID_STATUSES), load_default="todo")
    priority = fields.String(validate=validate.OneOf(VALID_PRIORITIES), load_default="medium")
    project_id = fields.Integer(required=True)
    assignee_id = fields.Integer(required=False, allow_none=True)
    due_date = fields.DateTime(required=False, allow_none=True)


class TaskUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(min=1, max=200))
    description = fields.String(allow_none=True)
    status = fields.String(validate=validate.OneOf(VALID_STATUSES))
    priority = fields.String(validate=validate.OneOf(VALID_PRIORITIES))
    assignee_id = fields.Integer(allow_none=True)
    due_date = fields.DateTime(allow_none=True)
