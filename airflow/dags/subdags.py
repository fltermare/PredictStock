import copy
import pendulum
import random

from airflow.models import DAG, settings
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from db_cmd import stock2df
#from twstock import Stock


def day_check(stock_code, start_record, last_record, **context):
    execution_date = context['execution_date']
    start_record = pendulum.parse(start_record)
    last_record = pendulum.parse(last_record)
    execution2start = execution_date - start_record
    execution2last = execution_date - last_record

    if not execution2start.invert and execution2last.invert:
        return 'no_do_nothing'
    else:
        return 'fetch_stock'


def fetch_stock(stock_code, **context):
    """use TWStock to get month data"""
    execution_date = context['execution_date']
    #stock = Stock(str(stock_code))
    #stock.fetch(execution_date.year, execution_date.month)
    #tmp = copy.deepcopy(stock)
    #return stock2df(tmp)
    return 'a'


def day_check_dag(parent_dag_name, child_dag_name, start_date, schedule_interval, infos):

    stock_code, start_record, last_record = infos

    dag = DAG(
        '%s.%s' % (parent_dag_name, child_dag_name),
        schedule_interval=schedule_interval,
        start_date=start_date,
    )

    dd = DummyOperator(
        task_id='no_do_nothing',
        dag=dag,
    )
    
    day_check_operator = BranchPythonOperator(
        task_id='day_check_%d' % stock_code,
        python_callable=day_check,
        provide_context=True,
        op_args=[stock_code, start_record, last_record],
        dag=dag,
    )

    #do_something_operator = DummyOperator(
    #    task_id="do_something_%d" % stock_code,
    #    dag=dag
    #)

    fetch_stock_operator = PythonOperator(
        task_id='fetch_stock',
        python_callable=fetch_stock,
        op_args=[stock_code],
        provide_context=True,
        dag=dag,
    )

    
    day_check_operator >> fetch_stock_operator >> dd
    day_check_operator >> dd

    return dag
