from flask import Flask
from core.config.config import config


def create_app(config_name):
    print('flask __name__:', __name__)
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    with app.app_context():
        # database
        from core.model.database import db
        db.init_app(app)

        # flask blueprint
        from core.controller.view import view_page
        app.register_blueprint(view_page)

        # dash application
        from core.model.dash_app import init_dashboard
        app = init_dashboard(app)

    return app
