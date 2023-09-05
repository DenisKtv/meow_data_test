import sqlite3

DATABASE_NAME = 'cheaters.db'


def create_table():
    """Создает таблицу с заданными полями в базе данных."""
    try:
        connection = sqlite3.connect(DATABASE_NAME)
        cursor = connection.cursor()

        create_table_query = '''CREATE TABLE IF NOT EXISTS data_table
                                (timestamp TEXT,
                                player_id INTEGER,
                                event_id INTEGER,
                                error_id INTEGER,
                                json_server TEXT,
                                json_client TEXT);'''

        cursor.execute(create_table_query)
        connection.commit()

    except sqlite3.Error as e:
        print(f'SQLite error: {e}')

    finally:
        if connection:
            connection.close()
