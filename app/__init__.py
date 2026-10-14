"""Application factory: builds and configures the Flask app."""
import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        # Override SECRET_KEY with an environment variable in any real deployment.
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "rethread.db"),
        UPLOAD_FOLDER=os.path.join(app.root_path, "static", "uploads"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5 MB upload limit
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    from . import models
    from .auth import bp as auth_bp
    from .shop import bp as shop_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(models.User, int(user_id))

    @app.context_processor
    def inject_cart_count():
        from flask import session
        return {"cart_count": len(session.get("cart", []))}

    from .seed import seed_command
    app.cli.add_command(seed_command)

    with app.app_context():
        db.create_all()

    return app
