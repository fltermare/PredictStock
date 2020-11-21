# from .. import db
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
import requests
import time
import pandas as pd

db = SQLAlchemy()


class Stock(db.Model):
    __tablename__ = 'stock'
    stock_code = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(30))
    first_record_date = db.Column(db.DateTime)
    last_record_date = db.Column(db.DateTime)

    def __init__(self, stock_code, name, first_record_date, last_record_date):
        self.stock_code = stock_code
        self.name = name
        self.first_record_date = first_record_date
        self.last_record_date = last_record_date


class History(db.Model):
    __tablename__ = 'history'
    date = db.Column(db.DateTime, primary_key=True)
    volume = db.Column(db.BigInteger, nullable=False)
    turnover = db.Column(db.BigInteger, nullable=True)
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)
    change = db.Column(db.Float, nullable=True)
    transactions = db.Column(db.BigInteger, nullable=True)
    stock_code = db.Column(db.String(20), primary_key=True)

    def __init__(self, date, volume, turnover, open, high, low, close, change, transactions, stock_code):
        self.date = date
        self.volume = volume
        self.turnover = turnover
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.change = change
        self.transactions = transactions
        self.stock_code = stock_code


def get_stock_list():
    """
    Return:
        res: list of stock code; List[str]
    """
    print("get_stock_list", id(db))
    query = db.session.query(Stock.stock_code).distinct()
    res = [s.stock_code for s in query]
    return res


def history_price(stock_codes=['0050']):
    """
    Args:
        stock_codes: list of stock codes

    Return:
        df: dataframe
    """

    print("history_price", id(db))
    # query = db.session.query(History.close, History.open).filter_by(stock_code=stock_code).all()
    # query = db.session.query(History).filter_by(stock_code=stock_code).order_by(History.date).all()

    # query = db.session.query(History).filter_by(stock_code=stock_code).order_by(History.date.desc())
    query = db.session.query(History).filter(History.stock_code.in_(stock_codes)).order_by(History.date.desc())
    print(type(query))
    # for _ in query:
    #     print(_.stock_code, _.date, _.close, _.open)
    df = pd.read_sql(sql=query.statement, con=db.session.bind)
    # print(df)

    return df


def query_stock_name(stock_code='0050'):
    print("query_stock_name", id(db))
    query = db.session.query(Stock).filter_by(stock_code=stock_code).distinct()

    print('----')
    for _ in query:
        print(_)
    print('----')
    return query[0].name


def get_options(list_stocks):
    dict_list = []
    for i in list_stocks:
        dict_list.append({'label': i, 'value': i})

    return dict_list


def get_available_stock_info():
    """
    Args:
        None

    Returns:
        res: [(stock_code, first record date, last record date)]; List[tuple]
             e.g.
                 [('006208.TW', '2012-06-22', '2020-11-19'), ...]
    """

    query = db.session.query(History.stock_code, db.func.min(History.date), db.func.max(History.date)).group_by(History.stock_code).all()
    res = []
    for code, first_date, last_date in query:
        res.append((code, first_date.strftime("%Y-%m-%d"), last_date.strftime("%Y-%m-%d")))

    return res


def add_new_stock(stock_code):
    # add to stock
    new_stock = Stock(stock_code, None, None, None)
    db.session.add(new_stock)

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        print("Failed to add" + err)

    # unpause airflow dag
    airflow_webserver_url = current_app.config['AIRFLOW_WEBSERVER']
    dag_id = "Dynamic_DAG_{stock_code}".format(stock_code=stock_code)
    unpause_url = "{airflow_webserver_url}/api/experimental/dags/{dag_id}/paused/false".format(airflow_webserver_url=airflow_webserver_url, dag_id=dag_id)

    time.sleep(2)
    a = requests.get(unpause_url)
    print(a)


def delete_stock(stock_code):

    # delete from stock and history
    history_objs = db.session.query(History).filter(History.stock_code==stock_code).delete()
    stock_objs = db.session.query(Stock).filter(Stock.stock_code==stock_code).delete()

    # delete airflow jobs
    airflow_webserver_url = current_app.config['AIRFLOW_WEBSERVER']
    dag_id = "Dynamic_DAG_{stock_code}".format(stock_code=stock_code)
    dag_url = "{airflow_webserver_url}/api/experimental/dags/{dag_id}".format(airflow_webserver_url=airflow_webserver_url, dag_id=dag_id)
    requests.delete(dag_url)


    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        print("Failed to delete" + err)
