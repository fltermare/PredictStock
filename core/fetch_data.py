import twstock
import copy
import time
import datetime
import os
import pandas as pd
from core.db import insert_new_data
from pathlib import Path

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


def check_exist(stock_code, year, update=False):
    current_year = datetime.datetime.today().year
    p = Path('./history')
    csv_path = p / stock_code / (str(year)+'.csv')
    if current_year == year and not update:
        """get latest stock history this year"""
        return False
    else:
        return csv_path.exists()
    
    
def stock_history(stock_code='2330', years=[2018]):
    """
    get specific stock history and save it
    `Args`
        stock_code: code of target stock
        years: a list of interested years 
    `Return`
        history_result: a dataframe of a stock's history
    """
    stock = twstock.Stock(stock_code)
    current_year = datetime.datetime.today().year
    current_month = datetime.datetime.today().month
    current_day = datetime.datetime.today().day

    for year in years:
        if check_exist(stock_code, year):
            print("[%s] year %d exists" % (stock_code, year))
            continue
        tmp_df_list = []
        for month in range(1, 13):
            if year == current_year and month > current_month:
                break
            stock.fetch(year, month)
            tmp = copy.deepcopy(stock)
            if not tmp:
                # if empty
                continue
            print('get %s'%stock_code, year, month)
            tmp_df_list.append(stock2df(tmp))
            time.sleep(15)
        history_result = pd.concat(tmp_df_list, ignore_index=True)
        if history_result.empty:
            print(stock_code, year, 'empty')
        else:
            dataframe2csv(stock_code, year, history_result)
        time.sleep(30)

    return history_result


def dataframe2csv(stock_code, year, stock_df):
    p = Path('./history')
    q = p / stock_code
    q.mkdir(exist_ok=True)
    csv_path = p / stock_code / (str(year)+'.csv')
    stock_df.to_csv(csv_path.resolve(), index=False)
    print('dataframe2csv saved', csv_path.resolve())


def load_stock_year_csv(stock_code, year):
    p = Path('./history')
    q = p / stock_code
    csv_path = p / stock_code / (str(year)+'.csv')
    stock_year_df = pd.read_csv(csv_path)
    return stock_year_df


def get_new_data(stock_code, last_date):

    stock = twstock.Stock(stock_code)
    today = datetime.datetime.today()
    last_date = datetime.datetime.strptime(last_date, "%Y-%m-%d")
    #print('\n-\n', last_date, type(last_date), '\n', today, type(today), '\n-')

    for year in range(last_date.year, (today.year + 1)):
        if year == last_date.year:
            start_month, end_month = last_date.month, 12
        elif year == today.year:
            start_month, end_month = 1, today.month
        else:
            start_month, end_month = 1, 12

        # Aggregate monthly new data
        tmp_df_list = []
        for month in range(start_month, end_month+1):
            stock.fetch(year, month)
            tmp = copy.deepcopy(stock)
            if not tmp:
                continue
            tmp_df_list.append(stock2df(tmp))
            time.sleep(10)
        updated_df = pd.concat(tmp_df_list, ignore_index=True)

        # Update Database
        insert_new_data(stock_code, updated_df)

        # Aggregate existed and new data
        if check_exist(stock_code, year, update=True):
            stock_year_df = load_stock_year_csv(stock_code, year)
            updated_df = pd.concat([stock_year_df, updated_df]).reset_index(drop=True).drop_duplicates()
        dataframe2csv(stock_code, year, updated_df)
