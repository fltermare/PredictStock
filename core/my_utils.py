import argparse


def get_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", help="initialize database", action="store_true")
    parser.add_argument("--start", help="start web serivce", action="store_true")
    parser.add_argument("--train", help="train new model based on current dataset", action="store_true")
    args = parser.parse_args()
    return args
