import configparser
from core.dataloader import DataLoader, DataGenerator
from core.db import get_available_stocks
from keras.models import Model
from keras.callbacks import ModelCheckpoint, EarlyStopping
from keras.layers import Input, Flatten, BatchNormalization, Activation, Dense
from keras.layers import Bidirectional, LSTM

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')
SEQ_LEN = int(CONFIG['ML']['SEQ_LEN'])
ML_MODLE_PATH = str(CONFIG['COMMON']['ML_MODLE_PATH'])


def RNN(input_shape, neuron=10, n_layers=3):
    input_layer = Input(input_shape)
    middle = BatchNormalization()(input_layer)
    for _ in range(n_layers-1):
        middle = Bidirectional(
                    LSTM(neuron, return_sequences=True),
                    merge_mode='concat')(middle)
        middle = BatchNormalization()(middle)
    middle = Flatten()(middle)
    middle = Dense(neuron, activation='relu')(middle)
    output = Dense(1)(middle)
    model = Model(inputs=input_layer, outputs=output)
    model.compile(loss='mse', optimizer='adam', metrics=['mse', 'mae', 'mape'])
    return model


def train_model():

    stock_codes = [str(x[0]) for x in get_available_stocks()]
    dataloader = DataLoader(stock_codes=stock_codes, seq_len=SEQ_LEN)
    train_generator = DataGenerator(dataloader, batch_size=5, mode='train')
    val_generator = DataGenerator(dataloader, batch_size=5, mode='valid')

    model = RNN(dataloader.get_shape())
    model.summary()
    early_stop = EarlyStopping(monitor='val_loss', patience=10)
    checkpointer = ModelCheckpoint(filepath=ML_MODLE_PATH, verbose=0, save_best_only=True)
    model.fit_generator(
        generator=train_generator,
        validation_data=val_generator,
        epochs=10,
        verbose=1,
        callbacks=[early_stop, checkpointer]
    )


if __name__ == "__main__":
    train_model()