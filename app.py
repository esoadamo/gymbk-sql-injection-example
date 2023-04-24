from typing import Optional

from flask import Flask, render_template, session, request, redirect, url_for
from database import Database

database = Database()
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'gymbk'


def get_username() -> Optional[str]:
    return session.get('username')


@app.route('/login', methods=["GET", "POST"])
def login():
    if get_username() is not None:
        return redirect(url_for('hello_world'))

    if request.method == 'POST':
        session['username'] = request.form['name']
        database.create_user(session['username'])
        return redirect(url_for('hello_world'))
    return render_template('login.html')


@app.route('/stats')
def stats():
    return render_template('stats.html',
                           stats=database.get_user_stats(),
                           transactions=database.get_transactions(),
                           log=database.get_log()
                           )


@app.route('/', methods=['GET', 'POST'])
def hello_world():  # put application's code here
    name = get_username()
    if name is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        target = int(request.form['target'])
        coins = int(request.form['coins'])
        message = request.form['message']
        database.transfer(name, target, coins, message)

    return render_template('index.html',
                           name=name,
                           coins=database.get_coins(name),
                           users=database.get_users(),
                           transactions=database.get_user_transactions(name))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8927)
