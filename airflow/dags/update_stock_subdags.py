import copy
import pendulum
import random

from airflow.models import DAG, settings
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from datetime import timedelta
from db_cmd import stock2df, Stock2
from db_cmd import save_stock_to_disk, insert_new_data, check_stock_day_exist


def day_check(stock_code, start_record, last_record, db_path, **context):
    execution_date = context['execution_date']
    start_record = pendulum.parse(start_record)
    last_record = pendulum.parse(last_record)
    execution2start = execution_date - start_record
    execution2last = execution_date - last_record

    is_existed = check_stock_day_exist(stock_code, execution_date, db_path)

    #if not execution2start.invert and execution2last.invert:
    if is_existed:
        print('[day_check]', stock_code, execution_date, '[skip]')
        return 'done'
    else:
        print('[day_check]', stock_code, execution_date, '[fetch]')
        return 'fetch_stock'


def fetch_stock(stock_code, **context):
    """ Get month data"""
    execution_date = context['execution_date']
    stock = Stock2(str(stock_code))
    stock.fetch(execution_date.year, execution_date.month)
    updated_df = stock2df(stock)

    print("[***************]%s" % stock_code, updated_df.shape)
    return updated_df


def update_db(stock_code, db_path, **context):
    """ """
    updated_df = context['task_instance'].xcom_pull(task_ids='fetch_stock')
    
    insert_new_data(int(stock_code), updated_df, db_path)

    print('[*******update_db********]', updated_df.shape)


def save2disk(stock_code, **context):
    """ Save fetched data to local disk """
    updated_df = context['task_instance'].xcom_pull(task_ids='fetch_stock')
    execution_date = context['execution_date']
    year = execution_date.year

    save_stock_to_disk(int(stock_code), updated_df, year)

    print('[*******save2disk********]', updated_df.shape)


def day_check_dag(parent_dag_name, child_dag_name, start_date, schedule_interval, infos):

    stock_code, start_record, last_record, db_path = infos

    dag = DAG(
        '%s.%s' % (parent_dag_name, child_dag_name),
        schedule_interval=schedule_interval,
        start_date=start_date,
    )

    done = DummyOperator(
        task_id='done',
        dag=dag,
    )
    
    day_check_operator = BranchPythonOperator(
        task_id='day_check_%d' % stock_code,
        python_callable=day_check,
        provide_context=True,
        op_args=[stock_code, start_record, last_record, db_path],
        dag=dag,
    )

    fetch_stock_operator = PythonOperator(
        task_id='fetch_stock',
        python_callable=fetch_stock,
        op_args=[stock_code],
        provide_context=True,
        retries=5,
        retry_delay=timedelta(minutes=1),
        dag=dag,
    )

    update_db_operator = PythonOperator(
        task_id='update_db',
        python_callable=update_db,
        op_args=[stock_code, db_path],
        provide_context=True,
        dag=dag,
    )

    save2disk_operator = PythonOperator(
        task_id='save2disk',
        python_callable=save2disk,
        op_args=[stock_code],
        provide_context=True,
        dag=dag,
    )



    #day_check_operator >> fetch_stock_operator >> [update_db_operator, save2disk_operator] >> done
    day_check_operator >> fetch_stock_operator >> [update_db_operator, save2disk_operator]
    day_check_operator >> done

    return dag
