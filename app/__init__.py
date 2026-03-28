from flask import Flask


def create_app():
    app = Flask(__name__)

    # Register blueprints
    from .dashboard.routes import main
    from .api.routes import api

    app.register_blueprint(main)
    app.register_blueprint(api)

    return app
