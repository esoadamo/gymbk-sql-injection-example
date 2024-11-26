import json
from sys import stderr
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
        self.__coins_sum = self.get_coins_sum()
        self.log(f'Starting sum of coins: {self.__coins_sum}')

    def log(self, message: str, **kwargs) -> None:
        message_timestamp = f"{datetime.now()}: {message}"
        params = dict(kwargs)
        params['$message'] = message
        print('[LOG]', json.dumps(params), file=stderr, flush=True)
        self.__log.appendleft(message_timestamp)
        self.__db.execute('INSERT INTO log("message") VALUES (?)', (message_timestamp,))

    def execute(self, command: str, params: tuple = ()) -> List[tuple]:
        command_adjusted = command
        for param in params:
            command_adjusted = command_adjusted.replace('?', f"'{param}'", 1)
        self.log(f'[SQL] {command_adjusted}', command=command, params=params)

        result = []
        for i, subcommand in enumerate(command.split(';')):
            if not subcommand.strip():
                continue
            print('[SQL]', json.dumps({'q': subcommand.replace('\n', ' ')}))
            result.extend(self.__db.execute(subcommand, params if i == 0 else ()))
            self.__db.commit()
        return result

    def create_user(self, username: str) -> None:
        starting_coins = 100
        self.__coins_sum += starting_coins
        self.log(f'New user has arrived! New sum of coins: {self.__coins_sum}', coins_sum=self.__coins_sum, username=username)
        self.execute('INSERT INTO users("name", "coins") VALUES (?, ?)', (username, starting_coins))
        self.__db.commit()

    def get_coins(self, username: str) -> float:
        return self.execute('SELECT coins FROM users WHERE name = ?', (username,))[0][0]

    def get_username(self, user_id: int) -> str:
        return self.execute('SELECT name FROM users WHERE id = ?', (user_id,))[0][0]

    def get_user_id(self, username: str) -> int:
        return self.execute('SELECT id FROM users WHERE name = ?', (username,))[0][0]

    def user_exists(self, username: str) -> bool:
        return len(self.execute('SELECT id FROM users WHERE name = ?', (username,))) > 0

    def get_other_users(self, username: str) -> list:
        return self.execute('SELECT id, name FROM users WHERE name != ?', (username,))

    def transfer(self, from_username: str, to: int, coins: float, message: str) -> None:
        self.log(f'Transfer of {coins} coins attempted to {to}', from_username=from_username, to=to, coins=coins, user_message=message)
        assert coins > 0
        coins_now = self.get_coins(from_username)
        from_id = self.get_user_id(from_username)
        assert coins_now >= coins
        assert from_id != to
        to_username = self.get_username(to)
        coins_target_now = self.get_coins(to_username)
        statement = f'INSERT INTO `transaction`("from", "to", "coins", "message") VALUES (?, ?, ?, "{message}")'
        self.execute(f'UPDATE users SET coins=? WHERE id=?', (coins_target_now + coins, to))
        self.execute(f'UPDATE users SET coins=? WHERE id=?', (coins_now - coins, from_id))
        self.execute(statement, (from_id, to, coins))
        self.__db.commit()

    def get_user_transactions(self, username: str) -> List[tuple]:
        uid = self.get_user_id(username)
        return self.execute("""SELECT name, coins, message FROM (
SELECT t.id, name, t.coins * -1 as coins, message FROM `transaction` as t INNER JOIN users as u ON t.`to` = u.id 
WHERE `from` = ? UNION SELECT t.id, name, t.coins as coins, message FROM `transaction` as t INNER JOIN users as u 
ON t.`from` = u.id  WHERE `to` = ? ) ORDER by id DESC""", (uid, uid))

    def get_user_stats(self) -> List[tuple]:
        return self.__db.execute('SELECT * FROM users ORDER BY coins DESC')

    def get_transactions(self) -> List[tuple]:
        return self.__db.execute('SELECT * FROM `transaction` ORDER BY id DESC')

    def get_log(self) -> List[str]:
        return list(self.__log)

    def get_coins_sum(self) -> float:
        return self.__db.execute('SELECT SUM(coins) FROM users;')[0][0] or 0

    def check_coin_sum(self) -> bool:
        return abs(self.__coins_sum - self.get_coins_sum()) < 0.1

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
