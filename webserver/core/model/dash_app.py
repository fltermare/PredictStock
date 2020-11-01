from dash import Dash
from dash.dependencies import Input, State, Output
# import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import string, random
from flask_caching import Cache
from datetime import datetime

from core.model.database import db
from core.model.database import get_stock_list, history_price, query_stock_name, get_options
import plotly.graph_objs as go
# import plotly.express as px


def init_dashboard(server):
    print('dash __name__:', __name__)
    print("init_dashboard", id(db))
    import os
    assets_path = os.getcwd() + '/core/static/assets'
    dash_app = Dash(
        name=__name__,
        server=server,
        routes_pathname_prefix='/dash/',
        # requests_pathname_prefix='/dash/',
        suppress_callback_exceptions=True,
        assets_folder=assets_path
        # external_stylesheets=[
        #     dbc.themes.BOOTSTRAP,
        #     'https://fonts.googleapis.com/css?family=Lato'
        # ]
        )
    print('aaaabbbb')

    # dash_app.index_string = html_layout

    # cache = Cache(
    #     app.server,
    #     config={
    #         'CACHE_TYPE': 'filesystem',
    #         'CACHE_DIR': 'cache-directory',
    #         'CACHE_THRESHOLD': 10  # should be equal to maximum number of active users
    #     })

    # dash_app.layout = html.Div(
    #     [dcc.Location(id='url', refresh=False),
    #      html.Div(id='index')])

    dash_app.layout = html.Div(
        children=[
            html.Div(
                className='row',
                children=[
                    html.Div(
                        className='four columns div-user-controls',
                        children=[
                            html.H2('DASH - STOCK PRICE'),
                            html.P('Pick one or more stocks from the dropdown below'),
                            html.Div(
                                className='div-for-dropdown',
                                children=[
                                    dcc.Dropdown(id='stockselector',
                                                options=get_options(get_stock_list()),
                                                multi=True,
                                                value=[sorted(get_stock_list())[0]],
                                                style={'backgroundColor': '#1E1E1E'},
                                                className='stockselector'
                                    ),
                                ],
                                style={'color': '#1E1E1E'}
                            ),
                        ]
                    ),
                    html.Div(
                        className='eight columns div-for-charts bg-grey',
                        children=[
                            dcc.Graph(id='timeseries', config={'displayModeBar': False}, animate=True)

                        ]
                    )
                ]
            )
        ]
    )


    # @cache.memoize()
    # def create_secret(key):
    #     return ''.join(
    #         random.choice(string.ascii_letters + string.digits)
    #         for x in range(100))

    init_callbacks(dash_app)

    return dash_app


def init_callbacks(dash_app):

    # Callback for timeseries price
    @dash_app.callback(Output('timeseries', 'figure'), [Input('stockselector', 'value')])
    def update_graph(selected_dropdown_value):
        data = []
        df_sub = history_price(get_stock_list())
        for stock in selected_dropdown_value:
            data.append(go.Scatter(x=df_sub[df_sub['stock_code'] == stock]['date'],
                                   y=df_sub[df_sub['stock_code'] == stock]['close'],
                                   mode='lines',
                                   opacity=0.7,
                                   name=stock,
                                   textposition='bottom center'))
        # traces = [trace1]
        # data = [val for sublist in traces for val in sublist]
        # print('trace1')
        # print(trace1)
        # print('data')
        # print(data)
        # data = trace1
        figure = {
            'data': data,
            'layout': go.Layout(
                        # colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
                        template='plotly_dark',
                        paper_bgcolor='rgba(0, 0, 0, 0)',
                        plot_bgcolor='rgba(0, 0, 0, 0)',
                        margin={'b': 15},
                        hovermode='x',
                        autosize=True,
                        title={'text': 'Stock Prices', 'font': {'color': 'white'}, 'x': 0.5},
                        xaxis={'range': [df_sub['date'].min(), df_sub['date'].max()]},
            ),
        }

        return figure



    @dash_app.callback(Output('index', 'children'), [Input('url', 'search')])
    def display_page(request_args):
        # if request_args:
        # rr = pd.Series(str(request_args)[1:].split('&')).str.split('=')
        # key = rr.str.get(0)
        # value = rr.str.slice(1, ).str.join('=')
        # if 'secret' in list(key) and value[key == 'secret'].iloc[0] == create_secret(str(datetime.now()).split(':')[0]):
            # Query Stock in DB
        stock_code_name = get_stock_list()
        print(stock_code_name)

        # Get selected stock_code from request_args
        # selected_stock_code = value[key == 'stock_code'].iloc[0]
        selected_stock_code = '0050'

        return html.Div([
            html.Label('Dropdown'),
            dcc.Dropdown(
                id='stock_code_input',
                options=[
                    # {'label': "(%s) %s" % (stock_code, stock_name), 'value': stock_code} for stock_code, stock_name in stock_code_name
                    {'label': "(%s)" % (stock_code), 'value': stock_code} for stock_code in stock_code_name
                ],
                value=selected_stock_code
            ),
            html.Label('Slider'),
            dcc.Slider(
                id='select_interval',
                min=0,
                max=6,
                marks={
                    1: '30 days',
                    2: '90 days',
                    3: 'half year',
                    4: '1 year',
                    5: 'all'},
                value=2,
            ),
            html.Br(),
            html.Div(id='target_div')
        ])
        # return html.Div('Error ! Forbidden !')


    @dash_app.callback(Output('target_div', 'children'), [Input('stock_code_input', 'value'), Input('select_interval', 'value')])
    def update_stock_trend(stock_code, select_interval):

        # Fetch name
        stock_name = query_stock_name(stock_code)

        # Fetch price
        df = history_price([stock_code])

        if df.empty:
            layout_title = 'Not Exist'
            x_data, y_data = [1], [1]
        else:
            layout_title = "(%s) %s" % (stock_code, stock_name)
            x_data, y_data = df['date'], df['close']
            if select_interval == 1:
                x_data, y_data = x_data[-30:], y_data[-30:]
            elif select_interval == 2:
                x_data, y_data = x_data[-90:], y_data[-90:]
            elif select_interval == 3:
                x_data, y_data = x_data[-180:], y_data[-180:]
            elif select_interval == 4:
                x_data, y_data = x_data[-365:], y_data[-365:]

        figure = {
                'data': [
                    {
                        'x': x_data,
                        'y': y_data,
                        'type': 'line',
                        'name': stock_code
                    },
                ],
                'layout': {
                    'title': layout_title,

                }
            }
        return dcc.Graph(figure=figure)

        # return dcc.Graph(
        #     figure={
        #         'data': [
        #             {
        #                 'x': x_data,
        #                 'y': y_data,
        #                 'type': 'line',
        #                 'name': stock_code
        #             },
        #         ],
        #         'layout': {
        #             'title': layout_title,

        #         }
        #     })
