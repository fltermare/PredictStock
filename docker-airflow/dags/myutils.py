import datetime
import json
import numpy as np
import pandas as pd
import requests


def query_yahoo_finance(stock_code, start, execution_date):

    # convert execution_date to timestamp
    execution_date = execution_date.format("%Y-%m-%d")
    element = datetime.datetime.strptime(execution_date,"%Y-%m-%d")
    end = int(datetime.datetime.timestamp(element))

    # for TW stock
    stock_code += '.TW'

    site = "https://query1.finance.yahoo.com/v8/finance/chart/{stock_code:s}?period1={start:d}&period2={end:d}&interval=1d&events=history".format(
                stock_code=stock_code, start= start, end=end)

    response = requests.get(site)
    data = json.loads(response.text)
    df = pd.DataFrame(data['chart']['result'][0]['indicators']['quote'][0],
                      index=pd.to_datetime(np.array(data['chart']['result'][0]['timestamp'])*1000*1000*1000))

    return df.dropna()


def check_stock_day_exist(stock_code, execution_date, config):

    # create database connection
    conn = config.db_conn()
    cursor = conn.cursor()

    query_sql = """
        SELECT EXISTS(
            SELECT 1
            FROM history as h
            WHERE h.stock_code = %(stock_code)s and h.date = %(date)s
        );
    """

    execution_date = execution_date.format("%Y-%m-%d")
    cursor.execute(query_sql, {'stock_code': stock_code, 'date': execution_date})
    result = cursor.fetchone()
    print('[check_stock_day_exist.month_record]', execution_date, result)

    # close database connection
    cursor.close()
    conn.close()

    return result[0]


