from flask import Blueprint, render_template
from core.model.database import get_stock_list, history_price

view_page = Blueprint('view_page', __name__, template_folder='templates')


@view_page.route('/auth')
def auths():
    return 'auth3'


@view_page.route('/db')
def db():
    # res = query_available_stock()
    res = history_price()
    return res

@view_page.route('/db2')
def db2():
    res = get_stock_list()
    return res


# @view_page.route('/dashboard')
# def dashboard():
#     res = get_available_stock()
#     return "dash"


@view_page.route('/')
def index():
    return render_template('home.html')
