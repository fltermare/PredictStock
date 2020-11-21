from flask import Blueprint, render_template, redirect, url_for, request, flash
from core.model.database import get_stock_list, history_price, query_stock_name, get_options
from core.model.database import get_available_stock_info, add_new_stock, delete_stock

view_page = Blueprint('view_page', __name__, template_folder='templates')


# @view_page.route('/3')
# def auths():
#     res = query_stock_name()
#     return 'auth3' + "[%s]" % res

# @view_page.route('/1')
# def db():
#     # res = query_available_stock()
#     res = history_price()
#     return 'db'

# @view_page.route('/2')
# def db2():
#     res = get_stock_list()
#     print(res)
#     print(get_options(res))
#     df_sub = history_price(get_stock_list())
#     print(df_sub)
#     print(sorted(get_stock_list())[0])
#     return str(res)


@view_page.route('/dashboard')
@view_page.route('/')
def dashboard():
    return render_template('dashboard.html', dash_url='/dash')


@view_page.route("/manage", methods=["GET", "POST"])
def manage():

    if request.method == "POST":
        print('--------------')
        add_new_stock(request.form['stock_code'])
        flash('[Added] Downloading Now', 'success')
        print('--------------')

    stock_info = get_available_stock_info()

    return render_template('manage.html', stock_info=stock_info)



@view_page.route("/remove/<string:stock_code>", methods=["POST"])
def remove(stock_code):

    try:
        delete_stock(stock_code)
        flash('Delete', 'success')
    except Exception as err:
        flash('Delete Failed' + err, 'danger')

    return redirect(url_for('view_page.manage'))


# @view_page.route('/')
# def index():
#     print(__name__)
#     return render_template('home.html')
