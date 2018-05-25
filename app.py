import json
import itertools
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 '
                  'Safari/537.36'}


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


def get_article(id):
    url = 'https://news-at.zhihu.com/api/4/news/{}'.format(id)
    r = requests.get(url, headers=HEADERS)
    return json.loads(r.text)


def get_latest():
    url = 'https://news-at.zhihu.com/api/4/news/latest'
    r = requests.get(url, headers=HEADERS)
    json_data = json.loads(r.text)
    date = json_data['date']
    top_stories = json_data['top_stories']
    for story in top_stories:
        article_data = get_article(story['id'])
        cur = g.db.execute('select id from entries where id=? ', (article_data['id']))
        if not cur.fetchone():
            g.db.execute('insert into article (article_id, data) values (?, ?)',
                         (story['id'], json.dumps(article_data)))


def get_before(date_before):
    url = 'https://news-at.zhihu.com/api/4/news/before/{}'.format(date_before)


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
