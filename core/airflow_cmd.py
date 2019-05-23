#!/usr/bin/env python
import os
import subprocess

def set_airflow_env():
    """ set environment variable for airflow"""

    
    dir_path = os.getcwd() + '/airflow'
    os.environ["AIRFLOW_HOME"] = dir_path
    print("[airflow] set env %s" % os.environ['AIRFLOW_HOME'])



def init_airflow_db():

    print('[*] start initialize airflow database')
    subprocess.Popen(["airflow", "initdb"])


def start_airflow():

    print('[airflow] started')

    #subprocess.Popen(["airflow", "webserver", "-p", "8080"])
    #subprocess.Popen(["airflow", "scheduler", "-D"])
