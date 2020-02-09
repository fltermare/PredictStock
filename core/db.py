#!/usr/bin/env python3

import configparser
import datetime
import glob
import os
import pandas as pd
import sqlite3
import twstock
import subprocess
from core.airflow_cmd import backfill_dag, clear_dag, unpause_stock_dag, remove_stock_dag
from passlib.hash import sha256_crypt

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')
DEFAULT_HISTORY_PATH = str(CONFIG['COMMON']['STOCK_HISTORY_PATH'])
DEFAULT_DB_PATH = str(CONFIG['COMMON']['DB_PATH'])
MAIN_DAG = str(CONFIG['AIRFLOW']['MAIN_DAG'])
DAG_FILE_NAME = "update_stock_{}.py"
DAG_NAME_FORMAT = "{}_stock_update"


def db_check_exist():
    """ check database exists"""

    if os.path.isfile(DEFAULT_DB_PATH):
        print('[!] Database already exists')
        query = input("Do you want to doNothing/Overwrite/Backup ([n]/o/b) ? ").lower()
        if query == 'o':
            # Overwrite
            os.remove(DEFAULT_DB_PATH)
        elif query == 'b':
            # Backup original database
            from time import gmtime, strftime
            timestamp = strftime("%Y%m%d_%H%M", gmtime())
            renamed_db = DEFAULT_DB_PATH + "." + timestamp
            os.rename(DEFAULT_DB_PATH, renamed_db)
        else:
            # Do nothing
            return True

    return False


def db_init():

    if db_check_exist():
        return

    connection = db_connect()
    cursor = connection.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute("""
        CREATE TABLE stock (
            stock_code TEXT PRIMARY KEY UNIQUE NOT NULL,
            name TEXT NOT NULL,
            first_record_date DATE,
            last_record_date DATE
        )""")
    cursor.execute("""
        CREATE TABLE year (
            stock_code TEXT NOT NULL,
            stock_year INTEGER NOT NULL,
            FOREIGN KEY (stock_code) REFERENCES stock(stock_code),
            PRIMARY KEY (stock_code, stock_year)
        )""")
    cursor.execute("""
        CREATE TABLE stock_history (
            stock_code TEXT NOT NULL,
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

    db_init_user_table()
    dump2db()


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
        stock = twstock.codes[stock_code]
        init_stock_tuple = (stock_code, stock.name)
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
    # Update
    update_stock_info()


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
    """get available stocks in db
    Returns:
        result: a list of tuple
                [(stock_code `str`, stock_name `str`), ...]
    """

    connection  = db_connect()
    cursor = connection.cursor()

    # Execute query
    query_sql = """SELECT stock_code, name FROM stock"""
    cursor.execute(query_sql)
    result = cursor.fetchall()

    connection.close()
    return result


def get_available_stock_info():

    connection  = db_connect()
    cursor = connection.cursor()

    # Execute query
    query_sql = """SELECT stock_code, name, first_record_date, last_record_date
                   FROM stock"""
    cursor.execute(query_sql)
    result = cursor.fetchall()

    connection.close()
    return result


def gen_start_dag(stock_code_list):

    def _create_dag(dag_path, base_dag_path):
        subprocess.call(["cp", base_dag_path, dag_path])
        subprocess.call(["sed", "-i", "s/SHOULD_BE_STOCK_CODE/{}/g".format(stock_code), dag_path])


    stock_code_list = (x[0] for x in stock_code_list)
    airflow_dir = os.environ['AIRFLOW_HOME']

    for stock_code in stock_code_list:
        dag_path = '/'.join([airflow_dir, 'dags', DAG_FILE_NAME.format(stock_code)])
        base_dag_path = '/'.join([airflow_dir, 'dags', 'update_stock_base'])
        if not os.path.isfile(dag_path):
            _create_dag(dag_path, base_dag_path)

        # Difference between stock_dag and base_dag
        diff_proc = subprocess.Popen(["diff", dag_path, base_dag_path], stdout=subprocess.PIPE)
        diff_output = subprocess.check_output(['wc', '-l'], stdin=diff_proc.stdout).decode()
        if str(4) not in diff_output:
            _create_dag(dag_path, base_dag_path)


def add_new_stock(stock_code, start_date):

    connection  = db_connect()
    cursor = connection.cursor()

    stock = twstock.codes[stock_code]
    stock_name = stock.name
    start_date = datetime.datetime.strptime(start_date, '%Y-%m')

    insert_sql = """ INSERT or REPLACE INTO stock (stock_code, name, first_record_date, last_record_date)
                            VALUES (?, ?, ?, ?)"""
    insert_sql_tuple = (stock_code, stock_name, start_date.strftime('%Y-%m-%d'), start_date.strftime('%Y-%m-%d'))
    cursor.execute(insert_sql, insert_sql_tuple)
    connection.commit()

    query_sql = """SELECT stock_code FROM stock"""
    cursor.execute(query_sql)
    stock_code_list = cursor.fetchall()
    connection.close()

    gen_start_dag(stock_code_list)

    backfill_end_time = datetime.date.today() - datetime.timedelta(days = 2)
    backfill_dag(DAG_NAME_FORMAT.format(stock_code), start_date.strftime('%Y-%m-%d'), datetime.datetime.strftime(backfill_end_time, "%Y-%m-%d"))


def delete_stock(stock_code):
    def _delete_frome_stock_history():
        delete_sql = """DELETE
                    FROM stock_history
                    WHERE stock_code = ?"""
        delete_sql_tuple = (stock_code,)
        cursor.execute(delete_sql, delete_sql_tuple)

    def _delete_from_stock():
        delete_sql = """DELETE
                    FROM stock
                    WHERE stock_code = ?"""
        delete_sql_tuple = (stock_code,)
        cursor.execute(delete_sql, delete_sql_tuple)

    def _delete_airflow_log():
        import shutil
        _ = [os.environ['AIRFLOW_HOME'], 'logs', "{}.day_check_dag_{}".format(MAIN_DAG, stock_code)]
        airflow_stock_log_dir = "/".join(_)
        shutil.rmtree(airflow_stock_log_dir, ignore_errors=True)
        _ = [os.environ['AIRFLOW_HOME'], 'logs', MAIN_DAG, "day_check_dag_{}".format(stock_code)]
        airflow_stock_log_dir = "/".join(_)
        shutil.rmtree(airflow_stock_log_dir, ignore_errors=True)

    def _clear_airflow_record(flag):
        query_sql = """
                SELECT MIN(date), MAX(date)
                FROM stock_history
                """
        #query_sql_tuple = (stock_code,)
        #cursor.execute(query_sql, query_sql_tuple)
        #if first:
        cursor.execute(query_sql)
        start_day, last_day = cursor.fetchone()
        print(start_day, last_day)
        print(type(start_day), type(last_day))
        task_id = ".".join([MAIN_DAG, "day_check_dag_%s" % stock_code])
        clear_dag(task_id, str(start_day), str(last_day), flag)

    def _delete_dag():
        dag_path = '/'.join([os.environ['AIRFLOW_HOME'], 'dags', DAG_FILE_NAME.format(stock_code)])
        try:
            os.remove(dag_path)
        except OSError:
            print("{} does not exist".format(dag_path))
        remove_stock_dag(DAG_NAME_FORMAT.format(stock_code))

    connection  = db_connect()
    cursor = connection.cursor()
    #_clear_airflow_record(flag=True)
    _delete_from_stock()
    _delete_frome_stock_history()
    _delete_airflow_log()
    _delete_dag()
    #_clear_airflow_record(flag=False)
    connection.commit()



def update_stock_info():

    connection  = db_connect()
    cursor = connection.cursor()
    query_sql = """SELECT stock_code FROM stock"""
    cursor.execute(query_sql)
    result = cursor.fetchall()

    if result:
        for code in result:
            query_sql = """
                SELECT MIN(date), MAX(date)
                FROM stock_history
                WHERE stock_history.stock_code = ?"""
            cursor.execute(query_sql, code)
            result = cursor.fetchone()

            update_sql = """
                UPDATE stock
                SET first_record_date = ?,
                    last_record_date = ?
                WHERE stock.stock_code = ?"""
            sql_tuple = (result[0], result[1], code[0])
            cursor.execute(update_sql, sql_tuple)
            connection.commit()

    connection.close()


def insert_new_data(stock_code, year_data):

    connection = db_connect()
    cursor = connection.cursor()
    for index, day_data in year_data.iterrows():
        #print(index, day_data)
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

    connection.close()