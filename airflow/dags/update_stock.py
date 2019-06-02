import configparser
import os
import time

from datetime import datetime, timedelta
from subdags import day_check_dag
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.subdag_operator import SubDagOperator
from db_cmd import db_connect
import sys

CONFIG = configparser.ConfigParser()
STOCK_HOME = os.environ['STOCK_HOME'] + '/'
CONFIG.read(STOCK_HOME + 'config.ini')
DB_PATH = STOCK_HOME + str(CONFIG['COMMON']['DB_PATH'])

MAIN_DAG = "stock_update_dag"
SUB_DAG = "day_check_dag"

default_args = {
    'owner': 'user',
    'retries': 2,
    'retry_delay': timedelta(minutes=1)
}


def get_stock_list(**context):
    connection = db_connect(DB_PATH)
    cursor = connection.cursor()

    query_sql = """SELECT stock_code, first_record_date, last_record_date
                    FROM stock"""
    cursor.execute(query_sql)
    result = cursor.fetchall()
    connection.close()
    return result


main_dag = DAG(
    dag_id=MAIN_DAG,
    default_args=default_args,
    start_date=datetime(2019, 5, 30, 0, 0),
    schedule_interval=timedelta(days=1)
)


dummy_start_operator = DummyOperator(
    task_id='start',
    dag=main_dag,
)

dummy_end_operator = DummyOperator(
    task_id="end",
    dag=main_dag
)

stock_list = get_stock_list()
for stock_code, start_record, last_record in stock_list:

    sub_dag = SUB_DAG + '_%d' % stock_code
    infos = [stock_code, start_record, last_record]

    day_check_subdag = SubDagOperator(
        subdag=day_check_dag(MAIN_DAG, sub_dag, main_dag.start_date, main_dag.schedule_interval, infos),
        task_id='day_check_dag_%d' % stock_code,
        dag=main_dag
    )

    dummy_start_operator >> day_check_subdag >> dummy_end_operator
