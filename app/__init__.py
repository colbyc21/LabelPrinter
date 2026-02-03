import os
from flask import Flask


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    from app.routes.main import bp as main_bp
    from app.routes.batch import bp as batch_bp
    from app.routes.adhoc import bp as adhoc_bp
    from app.routes.admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(batch_bp, url_prefix="/batch")
    app.register_blueprint(adhoc_bp, url_prefix="/adhoc")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.context_processor
    def inject_printers():
        from app.services.printer import get_printers
        return dict(printers=get_printers())

    return app
