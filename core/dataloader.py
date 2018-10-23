#!/usr/bin/env python3

import random
import numpy as np
import pandas as pd
from core.db import db_connect
from sklearn import preprocessing
from keras.utils import Sequence

class DataLoader():
    def __init__(self, stock_codes=[], seq_len=15, is_train=True):
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

        df[['ori_close', 'ori_change']] = df[['close', 'change']]
        df[normalize_columns] = self.scalers[stock_code].transform(df[normalize_columns])
        #print(df.head())
        return df

    def gen_scaler(self, stock_code, parts_df):
        """
        generate scaler for specific stock using all history data
        todo:
            - save scaler to disk
        """

        scaler = preprocessing.MaxAbsScaler().fit(parts_df.values)       
        parts_df= pd.DataFrame(scaler.transform(parts_df))
        self.scalers[stock_code] = scaler

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