#!/usr/bin/env python3
import configparser
#import config
import datetime
import random
import numpy as np
import pandas as pd
import pickle
from core.db import db_connect
from sklearn import preprocessing
from keras.utils import Sequence

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')
SEQ_LEN = int(CONFIG['ML']['SEQ_LEN'])
SCALERS_DIR_PATH = str(CONFIG['COMMON']['SCALERS_DIR_PATH'])


class DataLoader():
    def __init__(self, stock_codes=[], seq_len=SEQ_LEN, is_train=True):
        self.seq_len, self.is_train = seq_len, is_train
        self.scalers = dict()
        self.stock_codes = [str(x) for x in stock_codes if x.isdigit()]
        self.all_data, self.all_idxs = self.load_history()
        self.split_dataset()

    def load_history(self):
        connection = db_connect()
        #cursor = connection.cursor()
        tmp_df_list = []
        indexs = []
        count = 0
        for stock_code in self.stock_codes:
            query_sql = """
                        SELECT * FROM stock_history
                        WHERE stock_code=%s
                        ORDER BY stock_history.date
                        """ % stock_code
            df = pd.read_sql(query_sql, connection)
            df = self.add_feature(df)
            df = self.df_normalize(stock_code, df)
            tmp_df_list.append(df)
            indexs += list(range(count+1+self.seq_len, count+len(df)-1))
            count += len(df)

        connection.close()

        df = pd.concat(tmp_df_list, ignore_index=True)
        #parts = df.iloc[indexs, :]
        return df, indexs
    
    def split_dataset(self):
        np.random.shuffle(self.all_idxs)
        ratio = 0.8
        self.train_idxs = self.all_idxs[:int(len(self.all_idxs)*ratio)]
        tmp = self.all_idxs[int(len(self.all_idxs)*ratio):]
        self.valid_idxs = tmp[:int(len(tmp)*0.5)]
        self.test_idxs = tmp[int(len(tmp)*0.5):]
        print('train idxs', len(self.train_idxs))
        print('valid idxs', len(self.valid_idxs))
        print('test  idxs', len(self.test_idxs))

    def add_feature(self, df):
        """ add new features (previous/following trade day)
        """
        tmp_date = pd.to_datetime(df['date'])
        df.loc[:, 'previous_day'] = pd.to_numeric((tmp_date.diff().fillna(0).dt.days))
        df.loc[:, 'follow_day'] = pd.to_numeric((tmp_date.diff(periods=-1).fillna(0).dt.days).abs())
        return df

    def df_normalize(self, stock_code, df):
        """
        todo:
            - if is_train == False, load scaler from disk
        """
        normalize_columns = ['capacity', 'turnover', 'open', 'high', 'low', 'close', 'change', 'transactions']
        # gen scaler
        if self.is_train:
            self.gen_scaler(stock_code, df[normalize_columns])
        else:
            self.scalers[stock_code] = pickle.load(open(SCALERS_DIR_PATH+stock_code+".scaler", "rb"))

        df[['ori_close', 'ori_change']] = df[['close', 'change']]
        df[normalize_columns] = self.scalers[stock_code].transform(df[normalize_columns])
        #print(df.head())
        return df

    def gen_scaler(self, stock_code, parts_df):
        """
        generate scaler for specific stock using all history data
        todo:
            - save scaler to disk (done)
        """

        scaler = preprocessing.MaxAbsScaler().fit(parts_df.values)
        parts_df= pd.DataFrame(scaler.transform(parts_df))
        self.scalers[stock_code] = scaler
        pickle.dump(scaler, open(SCALERS_DIR_PATH+stock_code+".scaler", "wb"))

    def get_shape(self):
        return (self.seq_len, 10)


class DataGenerator(Sequence):
    def __init__(self, dataloader, batch_size=64, mode='train'):
        self.seq_len = dataloader.seq_len
        self.all_data = dataloader.all_data
        self.batch_size = batch_size
        if mode == 'train':
            self.df_idxs = dataloader.train_idxs
        elif mode == 'valid':
            self.df_idxs = dataloader.valid_idxs

    def __len__(self):
        return -(-len(self.df_idxs) // self.batch_size)
    
    def __getitem__(self, idx):
        batch_idxs = self.df_idxs[idx*self.batch_size:(idx+1)*self.batch_size]
        feature, target = [], []

        for idx in batch_idxs:
            # select seq_len + 1 days (predict target)
            tmp = self.all_data.iloc[idx-self.seq_len+1:idx+2, :]
            
            diff_close = tmp['ori_close'].iloc[-1] - tmp['ori_close'].iloc[0]
            diff_change = tmp['ori_change'].iloc[1:].sum()

            while not np.isclose(diff_close, diff_change):
                tt = list(batch_idxs)
                tt.remove(idx)
                new_random_idx = random.choice(tt)
                tmp = self.all_data.iloc[new_random_idx-self.seq_len+1:new_random_idx+2, :]
                diff_close = tmp['ori_close'].iloc[-1] - tmp['ori_close'].iloc[0]
                diff_change = tmp['ori_change'].iloc[1:].sum()
                #print('\n', idx, new_random_idx, len(tt))
                
                #print('[surprise] diff_change != diff_close' ,round(diff_close, 3), round(diff_change, 3))
                #print(tmp[['stock_code', 'date', 'ori_close', 'ori_change']])
                #random_idx = np.random.randint(0, self.__len__()-1)
                #return __getitem__(random_idx)

            target.append(round(diff_close, 3))

            feature_col = ['capacity', 'turnover', 'open', 'high', 'low', 'close', 'change', 'transactions', 'previous_day', 'follow_day']
            tmp = tmp[feature_col].iloc[:-1, :]
            
            feature.append(tmp.values)

        feature = np.array(feature)
        target = np.array(target)
        return feature, target


class PredictGenerator(Sequence, DataLoader):
    def __init__(self, stock_code, predict_date, seq_len=SEQ_LEN):
        self.seq_len, self.is_train = seq_len, False
        self.scalers = dict()
        self.stock_codes = [str(x) for x in [stock_code] if x.isdigit()]
        self.all_data, self.all_idxs = self.load_history()
        self.select_time_period(predict_date)

    def select_time_period(self, predict_date):
        idx = self.__date_valid(predict_date)

        # Select past `seq_len` data before predict_date
        self.selected_data = self.all_data.loc[list(range(idx-self.seq_len, idx)), :]
        print(self.all_data.loc[list(range(idx-self.seq_len, idx+1)), :])

    def __date_valid(self, predict_date):
        """
        Check whether the given date is valid
        - the date in the pass and is a trade date
        - the date of next trade date
        """
        self.all_data['date'] = pd.to_datetime(self.all_data['date'])
        predict_date = pd.Timestamp(predict_date)

        if predict_date in set(self.all_data['date']):
            idx = self.all_data.index[self.all_data['date']==predict_date].values
            idx = idx[0]
            self.real_predict_date = str(predict_date.strftime('%Y-%m-%d'))
        elif predict_date <= self.all_data.iloc[-1]['date']:
            # predict_date is in the pass
            idx = self.all_data.index[predict_date <= self.all_data['date']].values
            idx = idx[0]
            self.real_predict_date = str(self.all_data.iloc[idx]['date'].strftime('%Y-%m-%d'))
        else:
            # predict_date is in the future
            idx = self.all_data.index[-1] + 1
            self.real_predict_date = 'Next Trading Date'
        return int(idx)

    def ori_close(self):
        return self.selected_data.loc[:, 'ori_close'].values[0]

    def __len__(self):
        return 1

    def __getitem__(self, idx):
        feature_col = ['capacity', 'turnover', 'open', 'high', 'low', 'close', 'change', 'transactions', 'previous_day', 'follow_day']
        return np.array([self.selected_data[feature_col].values])