from core import create_app
from core.controller.view import view_page

app = create_app('localtest')
# app = create_app('development')
app.register_blueprint(view_page)
