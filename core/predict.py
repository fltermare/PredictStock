from core.dataloader import DataLoader
from core.db import db_connect

def stock_predict(model, stock_code, date):
    model.summary()
    print(stock_code, date)
    pass