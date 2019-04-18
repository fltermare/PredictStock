import argparse


def get_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", help="initialize database", action="store_true")
    parser.add_argument("--dump", help="dump stock price to database", action="store_true")
    args = parser.parse_args()
    return args