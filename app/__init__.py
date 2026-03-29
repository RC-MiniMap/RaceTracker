from flask import Flask
from flask_cors import CORS
import os


def create_app():
    app = Flask(__name__)

    # Enable CORS for Vite dev server
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    # Configuration
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "dev-secret-key-change-in-production"
    )

    # Register API blueprint — Flask is purely a JSON API
    from .api.routes import api

    app.register_blueprint(api, url_prefix="/api")

    return app
