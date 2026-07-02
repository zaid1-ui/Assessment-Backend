"""Consistent API response envelopes."""
from flask import jsonify


def success_response(data=None, message="Success", status_code=200, meta=None):
    body = {"success": True, "message": message, "data": data}
    if meta is not None:
        body["meta"] = meta
    return jsonify(body), status_code


def error_response(message="Error", status_code=400, errors=None):
    body = {"success": False, "message": message, "errors": errors}
    return jsonify(body), status_code
