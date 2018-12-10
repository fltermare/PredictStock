from dash import Dash
from dash.dependencies import Input, State, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import string, random
from flask_caching import Cache
from datetime import datetime

from core.db import db_connect, get_available_stocks


def display_stock(server):
    app = Dash(server=server, url_base_pathname='/dash/')
    app.config.supress_callback_exceptions = True

    cache = Cache(
        app.server,
        config={
            'CACHE_TYPE': 'filesystem',
            'CACHE_DIR': 'cache-directory',
            'CACHE_THRESHOLD':
            10  # should be equal to maximum number of active users
        })

    app.layout = html.Div(
        [dcc.Location(id='url', refresh=False),
         html.Div(id='index')])

    @cache.memoize()
    def create_secret(key):
        return ''.join(
            random.choice(string.ascii_letters + string.digits)
            for x in range(100))

    @app.callback(Output('index', 'children'), [Input('url', 'search')])
    def display_page(request_args):
        if request_args:
            rr = pd.Series(str(request_args)[1:].split('&')).str.split('=')
            key = rr.str.get(0)
            value = rr.str.slice(1, ).str.join('=')
            if 'secret' in list(key) and value[key == 'secret'].iloc[0] == create_secret(str(datetime.now()).split(':')[0]):
                # Query Stock in DB
                stock_code_name = get_available_stocks()

                return html.Div([
                    #dcc.Input(id='stock_code_input', type='stock_code', value='5880'),
                    dcc.Dropdown(
                        id='stock_code_input',
                        options=[
                            {'label': "(%s) %s" % (stock_code, stock_name), 'value': stock_code} for stock_code, stock_name in stock_code_name
                        ],
                        value=stock_code_name[0][0]
                    ),
                    html.Div(id='target_div')
                ])
        return html.Div('Error ! Forbidden !')

    @app.callback(Output('target_div', 'children'), [Input('stock_code_input', 'value')])
    def update_stock_trend(stock_code):

        connection = db_connect()
        query_sql = """
                    SELECT * FROM stock_history
                    WHERE stock_code=%s
                    ORDER BY stock_history.date
                    """ % stock_code
        df = pd.read_sql(query_sql, connection)
        connection.close()
        if df.empty:
            stock_code = 'Not Exist'
            x_data, y_data = [1], [1]
        else:
            x_data, y_data = df['date'], df['close']

        return dcc.Graph(
            figure={
                'data': [
                    {
                        'x': x_data,
                        'y': y_data,
                        'type': 'line',
                        'name': stock_code
                    },
                ],
                'layout': {
                    'title': stock_code
                }
            })

    return app.server, create_secret
