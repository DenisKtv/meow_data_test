import sqlite3

import pandas as pd

from database_setup import DATABASE_NAME, create_table
from memory_profiler import profile_memory_usage


class DataProcessor:
    def __init__(self):
        self.client_data = None
        self.server_data = None
        self.merged_data = None
        self.filtered_data = None

    def read_csv_by_date(self, file_path, date_column, target_date):
        df = pd.read_csv(file_path)
        df[date_column] = pd.to_datetime(df[date_column], unit='s')
        return df[df[date_column].dt.date == pd.Timestamp(target_date).date()]

    def load_data(self, client_file_path, server_file_path, target_date):
        self.client_data = self.read_csv_by_date(
            client_file_path,
            'timestamp',
            target_date
        )

        self.server_data = self.read_csv_by_date(
            server_file_path,
            'timestamp',
            target_date
        )

    def merge_data_by_error_id(self):
        if self.client_data is None or self.server_data is None:
            print("Client or server data not loaded.")
            return

        self.merged_data = pd.merge(
            self.client_data, self.server_data, on='error_id', how='inner',
            suffixes=('_client', '_server')
        )

        # Переименовать столбец timestamp
        self.merged_data.rename(
            columns={'timestamp_server': 'timestamp'}, inplace=True
        )

        # Удалить лишний столбец timestamp
        self.merged_data.drop(['timestamp_client'], axis=1, inplace=True)

        # Переименовать столбцы description
        self.merged_data.rename(
            columns={
                'description_client': 'json_client',
                'description_server': 'json_server'
            },
            inplace=True
        )

        columns_order = [
            'timestamp',
            'player_id',
            'event_id',
            'error_id',
            'json_server',
            'json_client'
        ]
        self.merged_data = self.merged_data[columns_order]

    def filter_cheaters(self):
        if self.merged_data is None:
            print("No merged data to filter.")
            return

        # Загрузка данных из таблицы cheaters в DataFrame
        connection = sqlite3.connect(DATABASE_NAME)
        cheaters_data = pd.read_sql('SELECT * FROM cheaters', connection)
        connection.close()

        # Преобразование ban_time и timestamp в формат datetime
        self.merged_data['timestamp'] = pd.to_datetime(
            self.merged_data['timestamp'], unit='s'
        )
        cheaters_data['ban_time'] = pd.to_datetime(cheaters_data['ban_time'])

        # Инициализация индексов для удаления
        to_remove = pd.Series([False] * len(self.merged_data))

        # Выбор player_id, которые нужно фильтровать
        cheater_ids = cheaters_data['player_id'].unique()

        # Сравнение времени бана и времени сервера
        for cheater_id in cheater_ids:
            ban_time = cheaters_data.loc[
                cheaters_data['player_id'] == cheater_id, 'ban_time'
            ].iloc[0]

            condition = (
                (self.merged_data['player_id'] == cheater_id) &
                (self.merged_data['timestamp'] < (ban_time + pd.Timedelta(
                    days=1)
                ))
            )
            to_remove = to_remove | condition

        self.merged_data = self.merged_data.loc[~to_remove]
        self.filtered_data = self.merged_data.copy()

    def insert_into_sqlite(self, table_name):
        if self.filtered_data is None:
            print('No filtered data to insert.')
            return

        connection = sqlite3.connect(DATABASE_NAME)
        self.filtered_data.to_sql(
            table_name, connection, if_exists='replace', index=False
        )
        connection.close()


if __name__ == '__main__':
    create_table()
    processor = DataProcessor()

    profile_memory_usage(
        processor.load_data,
        'client.csv',
        'server.csv',
        target_date='2021-04-21'
    )
    profile_memory_usage(processor.merge_data_by_error_id)
    profile_memory_usage(processor.filter_cheaters)
    profile_memory_usage(processor.insert_into_sqlite, 'data_table')
