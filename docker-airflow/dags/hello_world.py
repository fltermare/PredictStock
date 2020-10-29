"""
Code that goes along with the Airflow located at:
http://airflow.readthedocs.org/en/latest/tutorial.html
"""
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime, timedelta
from setting import Setting

SETTINGS = Setting()

default_args = {
    "owner": "Albert",
    "depends_on_past": False,
    "start_date": datetime(2020, 10, 20),
    "email": ["albert@airflow.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
}


# def create_dag(dag_id,
#                schedule,
#                default_args,
#                settings):
#     dag = DAG(dag_id, default_args=default_args, schedule_interval=schedule)
#     with dag:
#         init = DummyOperator(
#             task_id='Init',
#             dag=dag
#         )
#         clear = DummyOperator(
#             task_id='clear',
#             dag=dag
#         )
#         for stock_code in settings.stock_code_list:
#             tab = DummyOperator(
#                 task_id=stock_code,
#                 dag=dag
#             )
#             init >> tab >> clear
#         return dag

def create_dag(dag_id,
               schedule,
               default_args,
               stock_code):
    dag = DAG(dag_id, default_args=default_args, schedule_interval=schedule)
    with dag:
        init = DummyOperator(
            task_id='Init',
            dag=dag
        )
        done = DummyOperator(
            task_id='Done',
            dag=dag
        )
        tab = DummyOperator(
            task_id=stock_code,
            dag=dag
        )
        init >> tab >> done
        return dag

# schedule = "@hourly"
schedule = "0 */12 * * *"

for stock_code in SETTINGS.stock_code_list:
    dag_id = f"Dynamic_DAG_{stock_code}"
    globals()[dag_id] = create_dag(dag_id, schedule, default_args, stock_code)

