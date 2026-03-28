from flask import Flask
import os

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static')
    )
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Import and register blueprints
    from .dashboard.routes import main
    from .standings.routes import standings
    from .races.routes import races
    from .drivers.routes import drivers
    
    app.register_blueprint(main)
    app.register_blueprint(standings)
    app.register_blueprint(races)
    app.register_blueprint(drivers)
    
    return app
