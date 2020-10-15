# from .. import db
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

db = SQLAlchemy()

# def get_available_stock():
#     sql_cmd = """
#         SELECT *
#         FROM stock
#     """
#     query_data = db.engine.execute(sql_cmd)
#     print(query_data)
#     res = query_data.fetchall()

#     return str(res)


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
    capacity = db.Column(db.BigInteger, nullable=False)
    turnover = db.Column(db.BigInteger, nullable=False)
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)
    change = db.Column(db.Float, nullable=False)
    transactions = db.Column(db.BigInteger, nullable=False)
    stock_code = db.Column(db.String(20), primary_key=True)

    def __init__(self, date, capacity, turnover, open, high, low, close, change, transactions, stock_code):
        self.date = date
        self.capacity = capacity
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
