from core.dataloader import PredictGenerator
from core.db import db_connect

def stock_predict(model, graph, stock_code, date):

    predict_generator = PredictGenerator(stock_code, date)
    with graph.as_default():
        result = model.predict_generator(predict_generator)

    prediction = round(result[0][0]+predict_generator.ori_close(), 2)

    return prediction, predict_generator.real_predict_date