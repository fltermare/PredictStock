from dash import Dash
from dash.dependencies import Input, State, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import string, random
from flask_caching import Cache
from datetime import datetime

from core.db import db_connect

def display_stock(server):
    app = Dash(server=server, url_base_pathname='/dash/')
    app.config.supress_callback_exceptions = True

    cache = Cache(app.server, config={
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'cache-directory',
        'CACHE_THRESHOLD': 10  # should be equal to maximum number of active users
    })

    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='index')
    ])

    @cache.memoize()
    def create_secret(key):
        return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(100))

    @app.callback(
            Output('index', 'children'),
            [Input('url', 'search')])
    def display_page(request_args):
        if request_args:
            rr = pd.Series(str(request_args)[1:].split('&')).str.split('=')
            key = rr.str.get(0)
            value = rr.str.slice(1,).str.join('=')   
            if 'secret' in list(key) and value[key == 'secret'].iloc[0] == create_secret(str(datetime.now()).split(':')[0]):
                return  html.Div([
                            dcc.Input(id='input', type='stock_code', value=''),
                            html.Div(id='target')
                        ])
        return html.Div('Error ! Forbidden !')
    
    @app.callback(
            Output('target', 'children'),
            [Input('input', 'value')])
    def callback(stock_code):

        connection = db_connect()
        query_sql = """
                    SELECT * FROM stock_history
                    WHERE stock_code=%s
                    ORDER BY stock_history.date
                    """ % stock_code
        df = pd.read_sql(query_sql, connection)
        if len(df) == 0:
            stock_code = 'Not Exist'
            x_data, y_data = [1], [1]
        else:
            x_data, y_data = df['date'], df['close']
        connection.close()

        return dcc.Graph(
            figure={
                'data': [
                    {'x': x_data, 'y': y_data, 'type': 'line', 'name': stock_code},
                ],
                'layout': {
                    'title': stock_code
                }
            }
        )

    return app.server, create_secret