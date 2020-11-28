from flask import Blueprint, render_template, redirect, url_for, request, flash
from core.model.database import get_stock_list, history_price, query_stock_name, get_options
from core.model.database import get_available_stock_info, add_new_stock, delete_stock

view_page = Blueprint('view_page', __name__, template_folder='templates')


# @view_page.route('/get_test', methods=['GET'])
# def get_test():
#     name = request.values.get('name')
#     return 'GET: ' + str(name)


# @view_page.route('/post_test', methods=['POST'])
# def post_test():
#     var = request.values.get('var')
#     return 'POST: ' + str(var)


@view_page.route('/predict/<string:stock_code>', methods=['POST'])
def predict(stock_code):
    # NOT restful api
    # todo
    # check stock in DB
    # display price and prediction
    return stock_code


@view_page.route('/dashboard')
@view_page.route('/')
def dashboard():
    return render_template('dashboard.html', dash_url='/dash')


@view_page.route("/manage", methods=["GET", "POST"])
def manage():

    if request.method == "POST":
        print('--------------')
        stock_code = request.form['stock_code']
        add_new_stock(stock_code)
        flash("[Added] Downloading {} Now".format(stock_code), 'success')
        print('--------------')

    stock_info = get_available_stock_info()

    return render_template('manage.html', stock_info=stock_info)


@view_page.route("/remove", methods=["POST"])
def remove():

    stock_code = str(request.values.get('stock_code'))
    # method = request.values.get('_method')

    try:
        delete_stock(stock_code)
        flash("Delete {}".format(stock_code), 'success')
    except Exception as err:
        flash("Delete {} Failed".format(stock_code) + err, 'danger')

    return redirect(url_for('view_page.manage'))


# @view_page.route('/')
# def index():
#     print(__name__)
#     return render_template('home.html')
