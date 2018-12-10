#!/usr/bin/env python3
import configparser
import config
import dash
import io
import tensorflow as tf
from keras.models import load_model
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

from core.training import train_model
from core.predict import stock_predict
from core.db import db_register, db_user_login
from core.db import LoginException, get_available_stocks
from core import dash_app
from datetime import datetime

app = Flask(__name__)
app, create_secret = dash_app.display_stock(app)

model = None
graph = None
CUDA_VISIBLE_DEVICES=1
from keras.backend.tensorflow_backend import set_session
configuration = tf.ConfigProto()
configuration.gpu_options.per_process_gpu_memory_fraction = 0.3
set_session(tf.Session(config=configuration))


def load_ml_model():
    global model, graph
    model = load_model(config.ML_MODLE_PATH)
    graph = tf.get_default_graph()


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


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


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
@app.route('/register', methods=['Get', 'Post'])
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

        return redirect(url_for('index'))

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


### Dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
@is_logged_in
def dashboard():
    ### dash app
    dash_url = '/dash?secret={}'.format(create_secret(str(datetime.now()).split(':')[0]))

    # Get Stock Codes
    stock_code_name = get_available_stocks()

    if request.method == 'POST':
        # Get Form Value
        stock_code = request.form['stock_code']
        date = request.form['date']
        if not stock_code or not date:
            error = 'Please Select Stock and Date'
            return render_template('dashboard.html', error=error, dash_url=dash_url, stock_code_name=stock_code_name)

        # ML thing
        try:
            predict_price, real_predict_date = stock_predict(model, graph, stock_code, date)
        except:
            error = "Error Occured"
            return render_template('dashboard.html', error=error, dash_url=dash_url, stock_code_name=stock_code_name)

        # Return prediction
        prediction = dict()
        prediction['stock_code'] = stock_code
        prediction['date'] = real_predict_date
        prediction['price'] = predict_price
        #flash('You are now logged in', 'success')
        if real_predict_date != date:
            error = "%s is not a valid trading date" % date
            return render_template('dashboard.html', prediction=prediction, error=error, dash_url=dash_url, stock_code_name=stock_code_name)
        else:
            return render_template('dashboard.html', prediction=prediction, dash_url=dash_url, stock_code_name=stock_code_name)

    return render_template('dashboard.html', dash_url=dash_url, stock_code_name=stock_code_name)


def main():
    #train_model()
    load_ml_model()
    #stock_predict(model, '2834', '2018-08-03')
    #return
    print((" * Loading Keras model and Flask starting server..."
           "please wait until server has fully started"))

    app.secret_key = "secret123"
    app.run(debug=True)
