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


def backfill_dag(dag_id: str, start_time: str, end_time: str):
    subprocess.Popen(["airflow", "backfill", "-s", start_time, "-e", end_time, dag_id])


def start_airflow():

    print('[airflow] started')

    #subprocess.Popen(["airflow", "webserver", "-D", "-p", "8080"])
    #subprocess.Popen(["airflow", "scheduler", "-D"])
    subprocess.Popen(["airflow", "webserver", "-p", "8080"])
    subprocess.Popen(["airflow", "scheduler"])

    # How to kill airflow-scheduler & airflow-webserver
    # kill $(ps -ef | grep "airflow scheduler"|grep -v grep |awk '{print $2}')
    # kill $(ps -ef | grep "airflow webserver"|grep -v grep |awk '{print $2}')
    # kill $(ps -ef | grep "airflow scheduler"|grep -v grep |awk '{print $2}'); kill $(ps -ef | grep "airflow webserver"|grep -v grep |awk '{print $2}')