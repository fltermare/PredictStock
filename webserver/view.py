from flask import Blueprint
from core.db import get_available_stock

view_page = Blueprint('view_page', __name__, template_folder='templates')


@view_page.route('/auth')
def auths():
    return 'auth2'


@view_page.route('/')
def index():
    res = get_available_stock()
    return res
