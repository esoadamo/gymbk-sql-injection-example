from typing import Optional

from flask import Flask, render_template, session, request, redirect, url_for
from database import Database

database = Database()
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'gymbk'


def get_username() -> Optional[str]:
    saved = session.get('username')
    return saved if database.user_exists(saved) else None


@app.route('/login', methods=["GET", "POST"])
def login():
    if get_username() is not None:
        return redirect(url_for('hello_world'))

    if request.method == 'POST':
        username = request.form['name'].strip()
        assert not database.user_exists(username)
        database.create_user(username)
        session['username'] = username
        return redirect(url_for('hello_world'))
    return render_template('login.html')


@app.route('/stats')
def stats():
    return render_template('stats.html',
                           stats=database.get_user_stats(),
                           transactions=database.get_transactions(),
                           log=database.get_log(),
                           hacked=not database.check_coin_sum()
                           )


@app.route('/', methods=['GET', 'POST'])
def hello_world():  # put application's code here
    try:
        name = get_username()
    except IndexError:
        name = None

    if name is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        target = int(request.form['target'])
        coins = float(request.form['coins'])
        message = request.form['message']
        database.transfer(name, target, coins, message)

    return render_template('index.html',
                           name=name,
                           coins=database.get_coins(name),
                           users=database.get_other_users(name),
                           transactions=database.get_user_transactions(name))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8927)
