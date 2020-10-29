import os
import psycopg2
import pandas as pd


class Setting:
    def __init__(self):
        self.conn = self.db_conn()
        self.stock_code_list = self.select_all_stock_codes()        

    def db_conn(self):
        conn = psycopg2.connect(
            host='db',
            # host='localhost',
            database='db',
            user='postgres',
            password='postgres'
        )

        return conn

    def select_all_stock_codes(self):
        para_p_sql = """
            SELECT DISTINCT h.stock_code
            FROM history as h;
        """
        df = pd.read_sql(para_p_sql, con=self.conn)
        return sorted(df['stock_code'].values)

a = Setting()
print(a.stock_code_list)