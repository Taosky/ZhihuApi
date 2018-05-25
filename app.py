import os
import sqlite3
import requests
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
from flask_cors import CORS

app = Flask(__name__)
app.config['DATABASE'] = 'daily.db'
app.config['USERNAME'] = 'zxc'
app.config['PASSWORD'] = 'daily_zxc'
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
CORS(app)


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


# 应用环境销毁时执行
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    with app.app_context():
        # 建立了应用环境
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        # 释放关联并执行销毁函数


@app.before_request
def before_request():
    g.db = get_db()


def get_latest():




@app.route('/')
def show_entries():
    cur = g.db.execute('select title, text from entries order by id desc')
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))



if __name__ == '__main__':
    app.run(port=5661)
