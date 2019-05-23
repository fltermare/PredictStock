#!/usr/bin/env python3

from flask_server.app import run_server
from core.db import db_init, dump2db
from core.airflow_cmd import set_airflow_env, init_airflow_db, start_airflow
from core.my_utils import get_opt


def entry():
    args = get_opt()
    set_airflow_env()
    if args.init:
        db_init()
        init_airflow_db()

    if args.update:
        start_airflow()

    if args.start:
        run_server()
