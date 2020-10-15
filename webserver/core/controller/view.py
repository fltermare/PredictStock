from flask import Blueprint, render_template
from core.model.database import get_stock_list, history_price, query_stock_name, get_options

view_page = Blueprint('view_page', __name__, template_folder='templates')


@view_page.route('/3')
def auths():
    res = query_stock_name()
    return 'auth3' + "[%s]" % res

@view_page.route('/1')
def db():
    # res = query_available_stock()
    res = history_price()
    return 'db'

@view_page.route('/2')
def db2():
    res = get_stock_list()
    print(res)
    print(get_options(res))
    df_sub = history_price(get_stock_list())
    print(df_sub)
    print(sorted(get_stock_list())[0])
    return str(res)


@view_page.route('/4')
def dashboard():
    return render_template('dashboard.html', dash_url='/dash')


# @view_page.route('/dashboard')
# def dashboard():
#     res = get_available_stock()
#     return "dash"


@view_page.route('/')
def index():
    print(__name__)
    return render_template('home.html')
