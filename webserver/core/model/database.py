from .. import db


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

    query = db.session.query(Stock.stock_code).distinct()
    res = [s.stock_code for s in query]
    return str(res)


def history_price(stock_code='0050'):
    # query = db.session.query(History.close, History.open).filter_by(stock_code=stock_code).all()
    # query = db.session.query(History).filter_by(stock_code=stock_code).order_by(History.date).all()
    query = db.session.query(History).filter_by(stock_code=stock_code).order_by(History.date.desc()).all()
    print(len(query))
    for _ in query:
        print(_.stock_code, _.date, _.close, _.open)
    return str(len(query))
