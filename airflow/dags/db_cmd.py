import pandas as pd
import sqlite3

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