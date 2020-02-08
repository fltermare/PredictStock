#!/usr/bin/env python
import os
import subprocess

def set_airflow_env():
    """ set environment variable for airflow"""

    dir_path = os.getcwd() + '/airflow'
    os.environ["STOCK_HOME"] = os.getcwd()
    os.environ["AIRFLOW_HOME"] = dir_path
    print("[airflow] set env %s" % os.environ['AIRFLOW_HOME'])
    print("[stock] set env %s" % os.environ['STOCK_HOME'])



def init_airflow_db():

    print('[*] start initialize airflow database')
    subprocess.Popen(["airflow", "initdb"])
    from distutils.dir_util import copy_tree
    copy_tree("./core/dags", "airflow/dags")


def backfill_dag(dag_id: str, start_time: str, end_time: str):

    subprocess.Popen(["airflow", "backfill", "-l", "-x", "-B", "-s", start_time, "-e", end_time, dag_id])


def unpause_stock_dag(dag_id: str):
    subprocess.call(["airflow", "unpause", dag_id])


def remove_stock_dag(dag_id: str):
    subprocess.call(["airflow", "delete_dag", "-y", dag_id])


def clear_dag(dag_id: str, start_time: str, end_time: str, flag: bool):
    if flag:
        subprocess.call(["airflow", "clear", "--no_confirm", dag_id])
    else:
        subprocess.call(["airflow", "backfill", "--mark_success", "-s", start_time, "-e", end_time, "stock_update_dag"])
    #proc.poll()
    #subprocess.Popen(["airflow", "delete_dag", "-y", dag_id])



def start_airflow():

    print('[airflow] started')

    #subprocess.Popen(["airflow", "webserver", "-D", "-p", "8080"])
    #subprocess.Popen(["airflow", "scheduler", "-D"])
    subprocess.Popen(["airflow", "pool", "-s", "default_pool", "128", "default", "pool"])
    subprocess.Popen(["airflow", "webserver", "-p", "8080"])
    subprocess.Popen(["airflow", "scheduler"])

    # How to kill airflow-scheduler & airflow-webserver
    # kill $(ps -ef | grep "airflow scheduler"|grep -v grep |awk '{print $2}')
    # kill $(ps -ef | grep "airflow webserver"|grep -v grep |awk '{print $2}')
    # kill $(ps -ef | grep "airflow scheduler"|grep -v grep |awk '{print $2}'); kill $(ps -ef | grep "airflow webserver"|grep -v grep |awk '{print $2}')