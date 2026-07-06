"""Flask application factory."""
from flask import Flask
from flask_cors import CORS
from app.config import get_config
from app.extensions import db
from app.utils.logger import configure_logging
from app.utils.responses import error_response


def create_app(config_name: str = None):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    CORS(app, origins="*")

    db.init_app(app)
    configure_logging(app)

    register_blueprints(app)
    register_error_handlers(app)

    with app.app_context():
        # Ensure models are registered and tables exist (dev/test convenience;
        # in production use migrations, e.g. Flask-Migrate).
        from app import models  # noqa: F401
        db.create_all()

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app


def register_blueprints(app):
    from app.routes import user_routes, project_routes, task_routes, comment_routes, report_routes

    app.register_blueprint(user_routes.bp)
    app.register_blueprint(project_routes.bp)
    app.register_blueprint(task_routes.bp)
    app.register_blueprint(comment_routes.bp)
    app.register_blueprint(report_routes.bp)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return error_response("Resource not found", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response("Method not allowed", 405)

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.exception("Unhandled exception")
        return error_response("Internal server error", 500)