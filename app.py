from re import fullmatch
from typing import Optional
from time import sleep
from random import randint
from flask import Flask, render_template, session, request, redirect, url_for
from database import Database

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'gymbk'
secret_length = 12
database = Database(app, secret_length)


def get_username() -> Optional[str]:
    saved = session.get('username')
    return saved if database.user_exists(saved) else None


@app.route('/login', methods=["GET", "POST"])
def page_login():
    if get_username() is not None:
        return redirect(url_for('page_main'))

    if request.method == 'POST':
        username = request.form['name'].strip()

        if fullmatch(r'\d{' + str(secret_length) + '}', username):
            username = database.get_username_by_secret(username)
            if username is None:
                return render_template('login.html', error='Invalid secret code')
            session['username'] = username
            return redirect(url_for('page_main'))

        if database.user_exists(username):
            return render_template('login.html', error='User already exists')
        database.create_user(username)
        session['username'] = username
        return redirect(url_for('page_main'))

    return render_template('login.html')


@app.route('/stats')
def page_stats():
    return render_template('stats.html',
                           stats=database.get_user_stats(),
                           transactions=database.get_transactions(),
                           log=database.get_log(),
                           hacked=not database.check_coin_sum()
                           )


@app.route('/', methods=['GET', 'POST'])
def page_main():  # put application's code here
    try:
        name = get_username()
    except IndexError:
        name = None

    if name is None:
        return redirect(url_for('page_login'))

    error = ""

    if request.method == 'POST':
        target = int(request.form['target'])
        coins = float(request.form['coins'])
        message = request.form['message']
        try:
            database.transfer(name, target, coins, message)
            return redirect(url_for('page_main'))
        except AssertionError as e:
            error = str(e)

    return render_template('index.html',
                           name=name,
                           coins=database.get_coins(name),
                           users=database.get_other_users(name),
                           transactions=database.get_user_transactions(name),
                           error=error,
                           secret_code=database.get_user_secret(name)
                           )


@app.before_request
def gather_request_data():
    sleep(1 + randint(0, 30) / 10)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8927)
