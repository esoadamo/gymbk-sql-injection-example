from typing import List
from collections import deque
from datetime import datetime
from sqlitedb import SQLiteDB
from os import path


class Database:
    def __init__(self):
        file = 'data/db.sqlite3'
        init_db = not path.exists(file)
        self.__db = SQLiteDB(file)
        self.__log = deque()
        if init_db:
            self.create_database()
            self.log('First run')
        else:
            self.__log.extend(map(
                lambda x: x[0],
                self.__db.execute('SELECT message FROM log ORDER BY id DESC;')
            ))
            self.log('Started up')

    def log(self, message: str) -> None:
        message = f"{datetime.now()}: {message}"
        self.__log.appendleft(message)
        self.__db.execute('INSERT INTO log("message") VALUES (?)', (message,))

    def execute(self, command: str, params: tuple = ()) -> list[tuple]:
        command_adjusted = command
        for param in params:
            command_adjusted = command_adjusted.replace('?', f"'{param}'", 1)
        self.log(command_adjusted)
        return self.__db.execute(command, params)

    def create_user(self, username: str) -> None:
        self.execute('INSERT INTO users("name", "coins") VALUES (?, 100)', (username,))
        self.__db.commit()

    def get_coins(self, username: str) -> float:
        return self.execute('SELECT coins FROM users WHERE name = ?', (username,))[0][0]

    def get_username(self, user_id: int) -> str:
        return self.execute('SELECT name FROM users WHERE id = ?', (user_id,))[0][0]

    def get_user_id(self, username: str) -> int:
        return self.execute('SELECT id FROM users WHERE name = ?', (username,))[0][0]

    def get_users(self) -> list:
        return self.execute('SELECT id, name FROM users')

    def transfer(self, from_username: str, to: int, coins: float, message: str) -> None:
        coins_now = self.get_coins(from_username)
        from_id = self.get_user_id(from_username)
        assert coins_now >= coins
        assert from_id != to
        to_username = self.get_username(to)
        coins_target_now = self.get_coins(to_username)
        statement = f'INSERT INTO `transaction`("from", "to", "coins", "message") VALUES (?, ?, ?, "{message}")'
        print(statement)
        self.execute(statement, (from_id, to, coins))
        self.execute(f'UPDATE users SET coins=? WHERE id=?', (coins_target_now + coins, to))
        self.execute(f'UPDATE users SET coins=? WHERE id=?', (coins_now - coins, from_id))
        self.__db.commit()

    def get_user_transactions(self, username: str) -> list[tuple]:
        uid = self.get_user_id(username)
        return self.execute("""SELECT name, coins, message FROM (
SELECT t.id, name, t.coins * -1 as coins, message FROM `transaction` as t INNER JOIN users as u ON t.`to` = u.id 
WHERE `from` = ? UNION SELECT t.id, name, t.coins as coins, message FROM `transaction` as t INNER JOIN users as u 
ON t.`from` = u.id  WHERE `to` = ? ) ORDER by id DESC""", (uid, uid))

    def get_user_stats(self) -> list[tuple]:
        return self.__db.execute('SELECT * FROM users ORDER BY coins DESC')

    def get_transactions(self) -> list[tuple]:
        return self.__db.execute('SELECT * FROM `transaction` ORDER BY id DESC')

    def get_log(self) -> List[str]:
        return list(self.__log)

    def create_database(self) -> None:
        self.__db.execute('''CREATE TABLE "log" (
	"id"	INTEGER NOT NULL UNIQUE,
	"message"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
        self.execute('''CREATE TABLE "users" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL,
	"coins"	REAL NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
        self.execute('''CREATE TABLE "transaction" (
	"id"	INTEGER NOT NULL UNIQUE,
	"from"	INTEGER NOT NULL,
	"to"	INTEGER NOT NULL,
	"coins"	REAL NOT NULL,
	"message"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
