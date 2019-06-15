import airflow
import configparser
import os
import time

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.subdag_operator import SubDagOperator
from db_cmd import db_connect, update_stock_info
from update_stock_subdags import day_check_dag
import sys

CONFIG = configparser.ConfigParser()
STOCK_HOME = os.environ['STOCK_HOME'] + '/'
CONFIG.read(STOCK_HOME + 'config.ini')
DB_PATH = STOCK_HOME + str(CONFIG['COMMON']['DB_PATH'])

MAIN_DAG = str(CONFIG['AIRFLOW']['MAIN_DAG'])
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

    query_sql = """
                SELECT MIN(first_record_date)
                FROM stock"""
    cursor.execute(query_sql)
    dag_start_date = cursor.fetchone()
    dag_start_date = datetime.strptime(dag_start_date[0], "%Y-%m-%d")
    connection.close()
    print(dag_start_date)

    return result, dag_start_date


stock_list, dag_start_date = get_stock_list()
main_dag = DAG(
    dag_id=MAIN_DAG,
    default_args=default_args,
    #start_date=airflow.utils.dates.days_ago(1),
    start_date=dag_start_date,
    schedule_interval=timedelta(days=1)
)


update_stock_info_operator = PythonOperator(
    task_id='update_stock_info',
    python_callable=update_stock_info,
    op_args=[DB_PATH],
    dag=main_dag,
)

for stock_code, start_record, last_record in stock_list:

    sub_dag = SUB_DAG + '_%d' % stock_code
    infos = [stock_code, start_record, last_record, DB_PATH]
    #"""
    day_check_subdag = SubDagOperator(
        subdag=day_check_dag(MAIN_DAG, sub_dag, main_dag.start_date, main_dag.schedule_interval, infos),
        task_id='day_check_dag_%d' % stock_code,
        dag=main_dag
    )

    day_check_subdag >> update_stock_info_operator
    #"""
