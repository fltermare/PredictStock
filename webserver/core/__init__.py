from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from core.config.config import config
from core.plotlydash.dashboard import init_dashboard

db = SQLAlchemy()

def create_app(config_name):

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    app = init_dashboard(app)

    return app
