from .dataloader import DataLoader, DataGenerator
from keras.models import Model
from keras.layers import Input, Flatten, BatchNormalization, Activation, Dense
from keras.layers import Bidirectional, LSTM


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
    stock_codes = ['2834', '5880', '2892']
    dataloader = DataLoader(stock_codes=stock_codes, seq_len=15)
    train_generator = DataGenerator(dataloader, batch_size=5, mode='train')
    val_generator = DataGenerator(dataloader, batch_size=5, mode='valid')

    model = RNN(dataloader.get_shape())
    model.summary()
    model.fit_generator(
        generator=train_generator,
        validation_data=val_generator,
        epochs=100,
        verbose=1
    )

    pass


if __name__ == "__main__":
    train_model()