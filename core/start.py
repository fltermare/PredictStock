#!/usr/bin/env python3
from cmd import Cmd
from flask_server.app import run_server
from core.db import db_init, dump2db
from core.airflow_cmd import set_airflow_env, init_airflow_db, start_airflow
from core.my_utils import get_opt
from core.training import train_model


class MyPrompt(Cmd):

    prompt = "(Stock) "

    def do_hello(self, line):
        print('hello')

    def do_EOF(self, line):
        return True


def entry():
    args = get_opt()
    set_airflow_env()

    if args.init:
        db_init()
        init_airflow_db()

    if args.train:
        train_model()

    if args.update:
        start_airflow()

    if args.start:
        run_server()

    #MyPrompt().cmdloop()
