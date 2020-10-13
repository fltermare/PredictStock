from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from core.config.config import config

database = SQLAlchemy()

def create_app(config_name):

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    database.init_app(app)

    return app
