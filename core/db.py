#!/usr/bin/env python3

import config
import datetime
import glob
import pandas as pd
import sqlite3
import twstock
from passlib.hash import sha256_crypt

DEFAULT_HISTORY_PATH = config.STOCK_HISTORY_PATH
DEFAULT_DB_PATH = config.DB_PATH


def db_init():
    connection = db_connect()
    cursor = connection.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute("""
        CREATE TABLE stock (
            stock_code INTEGER PRIMARY KEY UNIQUE NOT NULL,
            name TXT NOT NULL
        )""")
    cursor.execute("""
        CREATE TABLE year (
            stock_code INTEGER NOT NULL,
            stock_year INTEGER NOT NULL,
            FOREIGN KEY (stock_code) REFERENCES stock(stock_code),
            PRIMARY KEY (stock_code, stock_year)
        )""")
    cursor.execute("""
        CREATE TABLE stock_history (
            stock_code INTEGER NOT NULL,
            date DATE NOT NULL,
            capacity INTEGER NOT NULL,
            turnover INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            change REAL NOT NULL,
            transactions INTEGER NOT NULL,
            FOREIGN KEY (stock_code) REFERENCES stock(stock_code),
            PRIMARY KEY (stock_code, date)
        )""")

    # testing
    #cursor.execute("INSERT INTO stock (stock_code, name, first_record_year, last_record_year) VALUES (?, ?, ?, ?)", (5566, '測試公司', 2008, 2018))
    #insert_test_sql = """ INSERT INTO stock_history (stock_code, date, capacity, turnover, open, high, low, close, change, transactions) 
    #          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    #task_1 = (5566, '2018-01-01', 1, 2, 3.1, 3.2, 3.0, 3.1, 0.7, 100)
    #cursor.execute(insert_test_sql, task_1)
    #task_2 = (5576, '2018-01-01', 1, 2, 3.1, 3.2, 3.0, 3.1, 0.7, 100)
    #cursor.execute(insert_test_sql, task_2)
    connection.commit()
    connection.close()


def db_connect(db_path=DEFAULT_DB_PATH):
    connection = sqlite3.connect(db_path)
    return connection


def stock_code_check(stock_code):
    connection = db_connect()
    cursor = connection.cursor()
    query_exist_sql = """SELECT stock_code FROM stock WHERE stock_code = ?"""
    cursor.execute(query_exist_sql, (stock_code,))
    result = cursor.fetchone()
    
    if not result:
    # new stock code
        insert_sql = """INSERT INTO stock (stock_code, name) VALUES (?, ?)"""
        stock = twstock.realtime.get(stock_code)
        init_stock_tuple = (stock_code, stock['info']['name'])
        cursor.execute(insert_sql, init_stock_tuple)
        connection.commit()
    connection.close()


def store_year_data(stock_code, year_data_file):
    connection = db_connect()
    cursor = connection.cursor()
    query_sql = """SELECT stock_year FROM year WHERE stock_code = ?"""
    cursor.execute(query_sql, (stock_code,))
    year_result = [row[0] for row in cursor.fetchall()]

    year = int(year_data_file[:-4].split('/')[-1])
    this_year = datetime.datetime.today().year

    if year not in year_result:
        # insert year record
        init_year_sql = """INSERT INTO year (stock_code, stock_year) VALUES (?, ?)"""
        init_year_sql_tuple = (stock_code, year)
        cursor.execute(init_year_sql, init_year_sql_tuple)
        connection.commit()
        #connection.close()
        #return
        
        # insert data record (per year)
        year_data = pd.read_csv(year_data_file)
        for index, day_data in year_data.iterrows():
            insert_sql = """ INSERT INTO stock_history (stock_code, date, capacity, turnover, open, high, low, close, change, transactions) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            insert_sql_tuple = (stock_code, day_data['date'], day_data['capacity'], day_data['turnover'],
                                day_data['open'], day_data['high'], day_data['low'], day_data['close'], 
                                day_data['change'], day_data['transaction'])
            cursor.execute(insert_sql, insert_sql_tuple)
            try:
                connection.commit()
            except:
                print('error')
    elif year == this_year:
        year_data = pd.read_csv(year_data_file)
        for index, day_data in year_data.iterrows():
            insert_sql = """ INSERT OR IGNORE INTO stock_history (stock_code, date, capacity, turnover, open, high, low, close, change, transactions) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            insert_sql_tuple = (stock_code, day_data['date'], day_data['capacity'], day_data['turnover'],
                                day_data['open'], day_data['high'], day_data['low'], day_data['close'], 
                                day_data['change'], day_data['transaction'])
            cursor.execute(insert_sql, insert_sql_tuple)
            try:
                connection.commit()
            except:
                print('error', index)
                break
        pass

    connection.close()


def dump2db(history_path=DEFAULT_HISTORY_PATH):
    stocks = glob.glob(history_path+'/*')
    stock_codes = [x.split('/')[-1] for x in stocks]
    for stock, stock_code in zip(stocks, stock_codes):
        stock_code_check(stock_code)

        data_files = glob.glob(stock+'/*')
        for year_data_file in data_files:          
            #continue
            store_year_data(stock_code, year_data_file)


def db_init_user_table():
    connection = db_connect()
    cursor = connection.cursor()

    #cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute("""
        CREATE TABLE users (
            username VARCHAR(30) UNIQUE NOT NULL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            password VARCHAR(100),
            register_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

    # testing
    #cursor.execute("INSERT INTO stock (stock_code, name, first_record_year, last_record_year) VALUES (?, ?, ?, ?)", (5566, '測試公司', 2008, 2018))
    #insert_test_sql = """ INSERT INTO stock_history (stock_code, date, capacity, turnover, open, high, low, close, change, transactions) 
    #          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    #task_1 = (5566, '2018-01-01', 1, 2, 3.1, 3.2, 3.0, 3.1, 0.7, 100)
    #cursor.execute(insert_test_sql, task_1)
    #task_2 = (5576, '2018-01-01', 1, 2, 3.1, 3.2, 3.0, 3.1, 0.7, 100)
    #cursor.execute(insert_test_sql, task_2)
    connection.commit()
    connection.close()


def db_register(username, name, email, password):
    connection  = db_connect()
    cursor = connection.cursor()

    # Execute query
    insert_sql = """INSERT INTO users(username, name, email, password) VALUES (?, ?, ?, ?)"""
    insert_sql_tuple = (username, name, email, password)
    cursor.execute(insert_sql, insert_sql_tuple)

    # Commit to DB
    connection.commit()

    # Close connection
    connection.close()

    return True


class LoginException(Exception):
    def __init__(self, msg):
        self.msg = msg


def db_user_login(username, password_candidate):
    connection = db_connect()
    # Get result as dict()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Execute query
    sql = """ SELECT * FROM users WHERE username = ?"""
    sql_tuple = (username, )
    cursor.execute(sql, sql_tuple)
    result = cursor.fetchone()

    # Commit to DB
    connection.commit()

    # Close connection
    connection.close()

    if result:
        password = result['password']
        if sha256_crypt.verify(password_candidate, password):
            # Pass
            pass
        else:
            raise LoginException("Password Mismatch")
    else:
        raise LoginException("User Not Found")


def get_available_stocks():
    connection  = db_connect()
    cursor = connection.cursor()

    # Execute query
    query_sql = """SELECT stock_code, name FROM stock"""
    cursor.execute(query_sql)
    result = cursor.fetchall()
    print(result)
    print(type(result))

    connection.close()
    return result
