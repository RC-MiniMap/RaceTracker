from flask import Flask
from flask_cors import CORS
import os



def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    # Enable CORS for Vite dev server
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    # Configuration
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "dev-secret-key-change-in-production"
    )

    # Import and register blueprints
    from .dashboard.routes import main

    # Register api blueprint (added below)
    from .api.routes import api
    app.register_blueprint(api, url_prefix="/api")

    app.register_blueprint(main)
    return app
