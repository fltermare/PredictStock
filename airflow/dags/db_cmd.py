import datetime
import os
import sqlite3
import urllib.parse
from collections import namedtuple
from pathlib import Path

import pandas as pd
import requests

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

STOCK_HOME = os.environ['STOCK_HOME'] + '/'
TWSE_BASE_URL = 'http://www.twse.com.tw/'
TPEX_BASE_URL = 'http://www.tpex.org.tw/'
DATATUPLE = namedtuple('Data', ['date', 'capacity', 'turnover', 'open',
                                'high', 'low', 'close', 'change', 'transaction'])


def db_connect(db_path):
    connection = sqlite3.connect(db_path)
    return connection


def stock2df(stock_m):
    """
    parse stock object and turn into dataframe

    `Args`
        stock_m: stock object including 1 month infomation
    `Returns`
        df_m: dataframe
    """
    columns = ['date', 'capacity', 'turnover', 'open', 'high', 'low', 'close', 'change', 'transaction']
    tmp_month_dict = {'date':[], 'capacity':[], 'turnover':[], 'open':[], 'high':[], 'low':[], 'close':[], 'change':[], 'transaction':[]}
    for oneday in stock_m.data:
        tmp_month_dict['date'].append(str(oneday.date.date()))
        tmp_month_dict['capacity'].append(oneday.capacity)
        tmp_month_dict['turnover'].append(oneday.turnover)
        tmp_month_dict['open'].append(oneday.open)
        tmp_month_dict['high'].append(oneday.high)
        tmp_month_dict['low'].append(oneday.low)
        tmp_month_dict['close'].append(oneday.close)
        tmp_month_dict['change'].append(oneday.change)
        tmp_month_dict['transaction'].append(oneday.transaction)
        
    df_m = pd.DataFrame(tmp_month_dict, columns=columns)
    return df_m


def check_stock_day_exist(stock_code, execution_date, db_path):
    def _is_current_month():
        return execution_date.format("%Y-%m") == datetime.datetime.today().strftime("%Y-%m")

    def _day_record_exist():
        query_sql = """SELECT EXISTS(
                        SELECT 1 FROM stock_history
                        WHERE stock_history.stock_code = ?
                        AND stock_history.date = ?
                        )"""
        query_sql_tuple = (stock_code, execution_date.format("%Y-%m-%d"))
        cursor.execute(query_sql, query_sql_tuple)
        result = cursor.fetchone()[0]
        print('[check_stock_day_exist.day_record]', execution_date.format("%Y-%m-%d"), result)
        return result

    def _month_record_exist():
        query_sql = """SELECT EXISTS(
                        SELECT 1 FROM stock_history
                        WHERE stock_history.stock_code = ?
                        AND strftime('%Y-%m', stock_history.date) = ?
                        )"""
        query_sql_tuple = (stock_code, execution_date.format("%Y-%m"))
        cursor.execute(query_sql, query_sql_tuple)
        result = cursor.fetchone()[0]
        print('[check_stock_day_exist.month_record]', execution_date.format("%Y-%m-%d"), result)
        return result

    def _day_off():
        if execution_date.is_sunday() or execution_date.is_saturday():
            return True

    def _later_than_latest_record():
        query_sql = """
                SELECT MAX(stock_history.date)
                FROM stock_history
                WHERE stock_history.stock_code = ?"""
        query_sql_tuple = (stock_code, )
        cursor.execute(query_sql, query_sql_tuple)
        latest_day = cursor.fetchone()[0]

        if latest_day:
            latest_day = datetime.datetime.strptime(latest_day, '%Y-%m-%d')
            result = execution_date > latest_day
        else:
            result = True

        print('[check_stock_day_exist.later_than]', execution_date.format("%Y-%m-%d"), result)
        return result

    connection  = db_connect(db_path)
    cursor = connection.cursor()

    ### Check current month
    if _day_off():
        flag = True
    elif _later_than_latest_record():
        flag = False
    elif _month_record_exist():
        flag = True
    else:
        flag = False

    connection.close()
    return flag


def check_exist(stock_code, year, update=False):
    current_year = datetime.datetime.today().year
    p = Path(STOCK_HOME + './history')
    csv_path = p / str(stock_code) / (str(year)+'.csv')

    if current_year == year and not update:
        """get latest stock history this year"""
        return False
    else:
        return csv_path.exists()


def dataframe2csv(stock_code, year, stock_df):
    p = Path(STOCK_HOME + './history')
    q = p / str(stock_code)
    q.mkdir(exist_ok=True)
    csv_path = p / str(stock_code) / (str(year)+'.csv')
    stock_df.to_csv(csv_path.resolve(), index=False)
    print('dataframe2csv saved', csv_path.resolve())


def load_stock_year_csv(stock_code, year):
    p = Path(STOCK_HOME + './history')
    q = p / str(stock_code)
    csv_path = p / str(stock_code) / (str(year)+'.csv')
    stock_year_df = pd.read_csv(csv_path)
    return stock_year_df


def update_stock_info(stock_code, db_path):

    connection  = db_connect(db_path)
    cursor = connection.cursor()
    print("[update_stock_info]", stock_code, type(stock_code))

    query_sql = """
        SELECT MIN(date), MAX(date)
        FROM stock_history
        WHERE stock_history.stock_code = ?"""
    cursor.execute(query_sql, (stock_code,))
    result = cursor.fetchone()
    print("[update_stock_info]", result)

    update_sql = """
        UPDATE stock
        SET first_record_date = ?,
            last_record_date = ?
        WHERE stock.stock_code = ?"""
    sql_tuple = (result[0], result[1], stock_code)
    cursor.execute(update_sql, sql_tuple)
    connection.commit()

    connection.close()



def save_stock_to_disk(stock_code: int, updated_df, year):

    if check_exist(stock_code, year, update=True):
        stock_year_df = load_stock_year_csv(stock_code, year)
        updated_df = pd.concat([stock_year_df, updated_df]).reset_index(drop=True).drop_duplicates()
    dataframe2csv(stock_code, year, updated_df)


def insert_new_data(stock_code, updated_df, db_path):

    connection = db_connect(db_path)
    cursor = connection.cursor()
    for _, day_data in updated_df.iterrows():

        insert_sql = """ INSERT OR IGNORE INTO stock_history (stock_code, date, capacity, turnover, open, high, low, close, change, transactions)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        insert_sql_tuple = (stock_code, day_data['date'], day_data['capacity'], day_data['turnover'],
                            day_data['open'], day_data['high'], day_data['low'], day_data['close'],
                            day_data['change'], day_data['transaction'])
        cursor.execute(insert_sql, insert_sql_tuple)

    connection.commit()
    connection.close()


##### Borrow from twstock code
class BaseFetcher(object):
    def fetch(self, year, month, sid, retry):
        pass

    def _convert_date(self, date):
        """Convert '106/05/01' to '2017/05/01'"""
        return '/'.join([str(int(date.split('/')[0]) + 1911)] + date.split('/')[1:])

    def _make_datatuple(self, data):
        pass

    def purify(self, original_data):
        pass


class TWSEFetcher(BaseFetcher):
    REPORT_URL = urllib.parse.urljoin(
        TWSE_BASE_URL, 'exchangeReport/STOCK_DAY')

    def __init__(self):
        pass

    def fetch(self, year: int, month: int, sid: str, retry: int=5):
        params = {'date': '%d%02d01' % (year, month), 'stockNo': sid}
        for retry_i in range(retry):
            r = requests.get(self.REPORT_URL, params=params)
            try:
                data = r.json()
            except JSONDecodeError:
                continue
            else:
                break
        else:
            # Fail in all retries
            data = {'stat': '', 'data': []}

        if data['stat'] == 'OK':
            data['data'] = self.purify(data)
        else:
            data['data'] = []
        return data

    def _make_datatuple(self, data):
        data[0] = datetime.datetime.strptime(
            self._convert_date(data[0]), '%Y/%m/%d')
        data[1] = int(data[1].replace(',', ''))
        data[2] = int(data[2].replace(',', ''))
        data[3] = None if data[3] == '--' else float(data[3].replace(',', ''))
        data[4] = None if data[4] == '--' else float(data[4].replace(',', ''))
        data[5] = None if data[5] == '--' else float(data[5].replace(',', ''))
        data[6] = None if data[6] == '--' else float(data[6].replace(',', ''))
        # +/-/X表示漲/跌/不比價
        data[7] = float(0.0 if data[7].replace(',', '') ==
                        'X0.00' else data[7].replace(',', ''))
        data[8] = int(data[8].replace(',', ''))
        return DATATUPLE(*data)

    def purify(self, original_data):
        return [self._make_datatuple(d) for d in original_data['data']]


class Stock2():
    def __init__(self, sid: str):
        self.sid = sid
        self.fetcher = TWSEFetcher()
        self.raw_data = []
        self.data = []

    def fetch(self, year: int, month: int):
        """Fetch year month data"""
        self.raw_data = [self.fetcher.fetch(year, month, self.sid)]
        self.data = self.raw_data[0]['data']
        #return self.data

    @property
    def date(self):
        return [d.date for d in self.data]

    @property
    def capacity(self):
        return [d.capacity for d in self.data]

    @property
    def turnover(self):
        return [d.turnover for d in self.data]

    @property
    def price(self):
        return [d.close for d in self.data]

    @property
    def high(self):
        return [d.high for d in self.data]

    @property
    def low(self):
        return [d.low for d in self.data]

    @property
    def open(self):
        return [d.open for d in self.data]

    @property
    def close(self):
        return [d.close for d in self.data]

    @property
    def change(self):
        return [d.change for d in self.data]

    @property
    def transaction(self):
        return [d.transaction for d in self.data]
