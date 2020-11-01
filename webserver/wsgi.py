# from werkzeug.middleware.dispatcher import DispatcherMiddleware
# from main import flask_app, dash_app


# application = DispatcherMiddleware(flask_app, {
#     '/dash': dash_app.server,
# })

from main import flask_app
application = flask_app.server
