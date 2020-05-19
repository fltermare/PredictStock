#!/usr/bin/env python3
import configparser
import dash
import io
import tensorflow as tf
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

from core.training import train_model
from core.predict import stock_predict
from core.db import db_register, db_user_login
from core.db import LoginException, get_available_stocks, get_available_stock_info, add_new_stock, delete_stock
from core import dash_app
from datetime import datetime

app = Flask(__name__)
app, create_secret = dash_app.display_stock(app)

model = None
# CUDA_VISIBLE_DEVICES=1
# from keras.backend.tensorflow_backend import set_session
# configuration = tf.compat.v1.ConfigProto()
# configuration.gpu_options.per_process_gpu_memory_fraction = 0.3
# set_session(tf.compat.v1.Session(config=configuration))

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')
ML_MODLE_PATH = str(CONFIG['COMMON']['ML_MODLE_PATH'])


def load_ml_model():
    global model
    model = tf.keras.models.load_model(ML_MODLE_PATH)


"""
def prepare_image(image, target):
    # if the image mode is not RGB, convert it
    if image.mode != "RGB":
        image = image.convert("RGB")

    # resize the input image and preprocess it
    image = image.resize(target)
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = imagenet_utils.preprocess_input(image)

    # return the processed image
    return image


@app.route("/predict", methods=["POST"])
def predict():
    # initialize the data dictionary that will be returned from the
    # view
    data = {"success": False}

    # ensure an image was properly uploaded to our endpoint
    if flask.request.method == "POST":
        if flask.request.files.get("image"):
            # read the image in PIL format
            image = flask.request.files["image"].read()
            image = Image.open(io.BytesIO(image))

            # preprocess the image and prepare it for classification
            image = prepare_image(image, target=(224, 224))

            # classify the input image and then initialize the list
            # of predictions to return to the client
            preds = model.predict(image)
            results = imagenet_utils.decode_predictions(preds)
            data["predictions"] = []

            # loop over the results and add them to the list of
            # returned predictions
            for (imagenetID, label, prob) in results[0]:
                r = {"label": label, "probability": float(prob)}
                data["predictions"].append(r)

            # indicate that the request was a success
            data["success"] = True

    # return the data dictionary as a JSON response
    return flask.jsonify(data)
"""


### Register Form Class
class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=3, max=25)])
    name = StringField('Name', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


### User Register
@app.route('/register', methods=['Get', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        name = form.name.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Insert to DB
        if db_register(username, name, email, password):
            flash("Your are now registered and can log in", 'success')

        return redirect(url_for('dashboard'))

    return render_template('register.html', form=form)


### User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Value
        username = request.form['username']
        password_candidate = request.form['password']
        try:
            db_user_login(username, password_candidate)
        except LoginException as e:
            # Failed to login
            app.logger.info(e.msg)
            error = "Invalid Login"
            return render_template('login.html', error=error)

        # Login Successful
        app.logger.info('PASS')
        session['logged_in'] = True
        session['username'] = username

        flash('You are now logged in', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')


### Check if user logged in
def is_logged_in(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return func(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap


### Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


### Dashboard & Homepage
@app.route('/', methods=['GET', 'POST'])
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    # Get Stock Codes
    stock_code_name = get_available_stocks()

    ### dash app
    dash_secret = create_secret(str(datetime.now()).split(':')[0])
    if not stock_code_name:
        # database is empty
        return render_template('home.html')
    dash_url = '/dash?secret={}&stock_code={}'.format(dash_secret, stock_code_name[0][0])

    if request.method == 'POST':
        # Get Form Value
        stock_code = request.form['stock_code']
        date = request.form['date']
        dash_url = '/dash?secret={}&stock_code={}'.format(dash_secret, stock_code)
        if not stock_code or not date:
            error = 'Please Select Stock and Date'
            return render_template('dashboard.html', error=error, dash_url=dash_url, stock_code_name=stock_code_name)

        # ML thing
        try:
            predict_price, real_predict_date = stock_predict(model, stock_code, date)
        except Exception as err:
            print(err)
            error = "Error Occured"
            return render_template('dashboard.html', error=error, dash_url=dash_url, stock_code_name=stock_code_name)

        # Reorder stock_code_name
        selected_stock_code_index = [i for i, v in enumerate(stock_code_name) if v[0] == stock_code].pop()
        selected_stock_code_name = stock_code_name.pop(selected_stock_code_index)
        stock_code_name.insert(0, selected_stock_code_name)

        # Return prediction
        prediction = dict()
        prediction['stock_code'] = stock_code
        prediction['stock_name'] = selected_stock_code_name[1]
        prediction['date'] = real_predict_date
        prediction['price'] = predict_price
        #flash('You are now logged in', 'success')
        if real_predict_date != date:
            error = "%s is not a valid trading date" % date
            return render_template('dashboard.html', prediction=prediction, error=error, dash_url=dash_url, stock_code_name=stock_code_name)
        else:
            return render_template('dashboard.html', prediction=prediction, dash_url=dash_url, stock_code_name=stock_code_name)

    return render_template('dashboard.html', dash_url=dash_url, stock_code_name=stock_code_name)


### Show Stock Info
@app.route('/manage', methods=["GET", "POST"])
@is_logged_in
def manage():

    if request.method == "POST":
        print('--------------')
        add_new_stock(request.form['stock_code'], request.form['first_month'])
        print('--------------')

    stock_info = get_available_stock_info()

    return render_template('manage.html', stock_info=stock_info)


### Fetch New Stock Price Data
@app.route('/fetch/<string:stock_code>/<string:last_date>', methods=['Post'])
@is_logged_in
def fetch(stock_code, last_date):

    try:
        delete_stock(stock_code)
        flash('Delete', 'success')
    except Exception as e:
        flash('Delete Failed' + e, 'danger')

    return redirect(url_for('manage'))


def run_server():

    load_ml_model()

    print((" * Loading Keras model and Flask starting server..."
           "please wait until server has fully started"))

    app.secret_key = "secret123"
    app.run(debug=False, host='0.0.0.0')
