from flask import Flask

def create_app():
  app = Flask(__name__)

  #import routes
  from .dashboard.routes import main
  app.register_blueprint(main)

  return app
