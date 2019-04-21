#!/usr/bin/env python3

from flask_server.app import run_server
from core.db import db_init, dump2db
from core.my_utils import get_opt


def entry():
    args = get_opt()
    if args.init:
        db_init()

    if args.start:
        run_server()
