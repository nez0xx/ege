import os
import sqlite3
from time import time

#os.remove('database.db')

class DataBase():
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        self.cursor = self.conn.cursor()

        self.get_users = lambda: self.get_all('users')
        self.get_replies = lambda: self.get_all('replies')

        self.get_chat = lambda chat_id: self.get('chats', 'CHAT_ID', chat_id)
        self.get_chat_timer = lambda chat_id: self.get('timers', 'CHAT_ID', chat_id)
        self.get_chat_greeting = lambda chat_id: self.get('greetings', 'CHAT_ID', chat_id)
        self.get_reply = lambda title: self.get('replies', 'TITLE', title)

        self.add_chat = lambda chat_id: self.add('chats', chat_id)
        self.add_reply = lambda title, description, photo, keyboard: self.add('replies', title, description, photo, keyboard)
        self.add_user = lambda user_id, username, first_name, last_name: self.add('users', user_id, username, first_name, last_name)

        self.set_greeting = lambda chat_id, text, photo, keyboard: self.add('greetings', chat_id, text, photo, keyboard)
        self.set_timer = lambda chat_id, text, photo, keyboard, delay, started: self.add('timers', chat_id, text, photo, keyboard, delay)

        self.delete_user = lambda user_id: self.delete('users', 'USER_ID', user_id)
        self.delete_timer = lambda chat_id: self.delete('timers', 'CHAT_ID', chat_id)
        self.delete_greeting = lambda chat_id: self.delete('greetings', 'CHAT_ID', chat_id)
        self.delete_reply = lambda title: self.delete('replies', 'TITLE', title)

        users_table = """CREATE TABLE IF NOT EXISTS users (
                            USER_ID int PRIMARY KEY,
                            USERNAME text,
                            FIRST_NAME text,
                            LAST_NAME text
                        ); """
        chats_table = """CREATE TABLE IF NOT EXISTS chats (
                            CHAT_ID int PRIMARY KEY,
                            CHANNEL_ID text DEFAULT NULL,
                            JOINED_LEFT boolean DEFAULT FALSE,
                            SYMBOL int CHECK (100 <= SYMBOL AND SYMBOL < 4000),
                            ANTIFLOOD int CHECK (2 <= ANTIFLOOD AND ANTIFLOOD <= 10),
                            BLOCK_CHANNELS boolean DEFAULT FALSE,
                            BLOCK_FORWARD boolean DEFAULT FALSE
                        ); """
        greetings_table = """CREATE TABLE IF NOT EXISTS greetings (
                            CHAT_ID int PRIMARY KEY,
                            TEXT text,
                            PHOTO text,
                            KEYBOARD text,
                            FOREIGN KEY (CHAT_ID) REFERENCES chats(CHAT_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                            CHECK(length(TEXT) > 0 OR length(PHOTO) > 0)
                        ); """
        timers_table = """ CREATE TABLE IF NOT EXISTS timers (
                            CHAT_ID int PRIMARY KEY,
                            TEXT text,
                            PHOTO text,
                            KEYBOARD text,
                            DELAY int NOT NULL CHECK (1 <= DELAY AND DELAY <= 20),
                            STARTED boolean DEFAULT FALSE,
                            FOREIGN KEY (CHAT_ID) REFERENCES chats(CHAT_ID) ON DELETE CASCADE ON UPDATE CASCADE
                            
                        ); """   
        replies_table = """CREATE TABLE IF NOT EXISTS replies (
                            TITLE text PRIMARY KEY,
                            DESCRIPTION text,
                            PHOTO text,
                            KEYBOARD text
                        ); """
        messages_table = """CREATE TABLE IF NOT EXISTS messages (
                            ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            CHAT_ID int,
                            MESSAGE_ID int,
                            FROM_USER int,
                            TIME int
                        ); """

        for table in (users_table, chats_table, greetings_table, timers_table, replies_table, messages_table, "PRAGMA foreign_keys=ON"):
            self.cursor.execute(table)

        self.add_user('749234118', 'zahardimidov', 'Zahar', 'Dimidov')
        self.cursor.fetchall()

    def get_all(self, table_name) -> list:
        self.cursor.execute(f'SELECT * FROM {table_name}')
        return self.cursor.fetchall()

    def add(self, table_name, *args) -> None:
        count = len([description[0] for description in self.cursor.execute(f'SELECT * FROM {table_name}').description])
        fields = ('?, '*count)[:-2]
        self.cursor.execute(f'INSERT OR REPLACE INTO {table_name} VALUES({fields});', args+(None,)*(count-len(args)))
        self.conn.commit()

    def delete(self, table_name, key, value) -> None:
        self.cursor.execute(f'DELETE FROM {table_name} WHERE {key} = ?', (value,)) 
        self.conn.commit()
    
    def get(self, table_name, key, value) -> dict:
        self.cursor.execute(f'SELECT * FROM {table_name} WHERE {key} = ?', (value,))
        return next((x for x in self.cursor.fetchall() if x), None)

    def get_field(self, table_name, field, key, value) -> dict:
        self.cursor.execute(f'SELECT {field} FROM {table_name} WHERE {key} = ?', (value,))
        return next((x for x in self.cursor.fetchall() if x), None)

    def set_chat_value(self, chat_id, key, value) -> None:
        self.cursor.execute(f'UPDATE chats SET {key} = ? WHERE CHAT_ID = ?', (value, chat_id))
        self.conn.commit()

    def add_message(self, chat_id, message_id, from_user):
        self.cursor.execute(f'INSERT OR REPLACE INTO messages(CHAT_ID, MESSAGE_ID, FROM_USER, TIME) VALUES(?, ?, ?, ?);', (chat_id, message_id, from_user, time(),))
        self.conn.commit()

    def get_last_messages(self, chat_id: int, n: int):
        self.cursor.execute(f'DELETE FROM messages WHERE CHAT_ID = ? AND ID NOT IN (SELECT ID FROM messages WHERE CHAT_ID = ? ORDER BY -TIME LIMIT ?)', (chat_id, chat_id, n,)) 
        self.conn.commit()
        self.cursor.execute(f'SELECT FROM_USER, TIME FROM messages WHERE CHAT_ID = ? ORDER BY -TIME LIMIT ?;', (chat_id, n,))
        return self.cursor.fetchall()

    def off_timers(self):
        self.cursor.execute(f'UPDATE timers SET STARTED = ?', (False,))
        self.conn.commit()

db = DataBase('database.db')
