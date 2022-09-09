import os
import sys

from dotenv import dotenv_values
from flask import Flask
from flask_alembic import Alembic
from flask_jwt_extended import JWTManager
from flask_rest_api import Api

from blueprints.docs import docs_bp
from extensions import db


def get_config():
    testing = any(["pytest" in arg for arg in sys.argv])
    env_file = ".env" if not testing else ".env_test"
    config = {
        **os.environ,
        **dotenv_values(env_file),
    }
    return config


def create_app():
    config = get_config()

    app = Flask(__name__)
    app.config.update(config)
    app.config["JWT_PUBLIC_KEY"] = open(config["JWT_PUBLIC_KEY_PATH"]).read()
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}@"
        f"{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_NAME']}"
    )

    db.init_app(app)
    JWTManager(app)
    api = Api(app)
    api.register_blueprint(docs_bp)

    alembic = Alembic()
    alembic.init_app(app)
    with app.app_context():
        alembic.upgrade()
        # alembic.revision(message="Create Doc model")

    return app

