import hmac
import os
from datetime import datetime, timedelta
import json
import itertools
import sqlite3
from subprocess import Popen

import requests
from flask import Flask, g, make_response, request
import hashlib
import PyRSS2Gen
from flask_cors import CORS

from utils import parse_ymd, replace_unsafe_img

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


def get_json_data(url):
    r = requests.get(url, headers=HEADERS)
    text = replace_unsafe_img(r.text)
    return json.loads(text)


def get_article(_id):
    url = 'https://news-at.zhihu.com/api/4/news/{}'.format(_id)
    return get_json_data(url)


def get_latest():
    with app.app_context():
        # 建立了应用环境
        db = get_db()
        url = 'https://news-at.zhihu.com/api/4/news/latest'
        json_data = get_json_data(url)
        date = json_data['date']
        top_stories = json_data['top_stories']
        stories = json_data['stories']
        for story in itertools.chain(top_stories, stories):
            cur = db.execute('select id from article where article_id=? ', (story['id'],))
            if not cur.fetchone():
                article_data = get_article(story['id'])
                db.execute('insert into article (article_id, data) values (?, ?)',
                           (story['id'], json.dumps(article_data)))
        cur_day = db.execute('select date from day where date=? ', (str(date),))
        if not cur_day.fetchone():
            db.execute('insert into day (date,data) values (?, ?)', (str(date), json.dumps(json_data)))
            text = 'Inserted'
        else:
            db.execute("update day set data = ? where date = ?", (json.dumps(json_data), str(date)))
            text = 'Updated'
        db.commit()
        db.close()
        return text


def get_before(date_before):
    with app.app_context():
        db = get_db()
        url = 'https://news-at.zhihu.com/api/4/news/before/{}'.format(date_before)
        json_data = get_json_data(url)
        date = json_data['date']
        db.execute('insert or replace into day (date, data) values (?, ?)', (date, json.dumps(json_data)))

        for story in json_data['stories']:
            cur = db.execute('select id from article where article_id=? ', (story['id'],))
            if not cur.fetchone():
                article_data = get_article(story['id'])
                db.execute('insert into article (article_id, data) values (?, ?)',
                           (story['id'], json.dumps(article_data)))

        db.commit()
        db.close()


@app.route('/v1/day/<date>')
def show_day(date):
    cur = g.db.execute('select data from day where date=?', (date,))
    r = cur.fetchone()
    if r:
        return r[0]
    before_date = (parse_ymd(date) + timedelta(days=1)).strftime('%Y%m%d')
    get_before(before_date)
    cur = g.db.execute('select data from day where date=?', (date,))
    return cur.fetchone()[0]


@app.route('/v1/article/<a_id>')
def show_article(a_id):
    cur = g.db.execute('select data from article where article_id=?', (a_id,))
    return cur.fetchone()[0]


@app.route('/v1/update')
def update():
    text = get_latest()
    return text


@app.route('/v1/zhuanlan/<name>/update')
def update_zhuanlan_rss(name):
    api = 'https://www.zhihu.com/api/v4/columns/{}/articles'.format(name)
    data = get_json_data(api)['data']

    items = []
    for article in data:
        item = PyRSS2Gen.RSSItem(
            title=article['title'],
            link=article['url'],
            description=article['excerpt'],
            guid=article['url'],
            pubDate=datetime.datetime.fromtimestamp(int(article['created'])),
        )
        items.append(item)

    rss = PyRSS2Gen.RSS2(
        title="知乎专栏-{}".format(name),
        link="https://zhuanlan.zhihu.com/{}".format(name),
        description="知乎专栏-{}".format(name),

        lastBuildDate=datetime.datetime.now(),
        items=items)

    rss.write_xml(open('zhuanlan/{}'.format(name), 'w', encoding='utf-8'))

    return 'Updated'


@app.route('/v1/zhuanlan/<name>/rss')
def show_zhuanlan_rss(name):
    xml_file = 'zhuanlan/{}'.format(name)
    if not os.path.exists(xml_file):
        return '404', 404

    resp = make_response(open(xml_file, encoding='utf-8').read())
    resp.headers["Content-type"] = "application/xml;charset=UTF-8"
    return resp


@app.route('/v1/webhook', methods=['POST'])
def webhook():
    secret = 'taoskycn'
    if 'X-Hub-Signature' in request.headers and request.headers['X-Hub-Signature'].startswith('sha1='):
        p=Popen('/var/www/Daily/webhook.sh')
        return 'Ok'
    else:
        return 'Forbidden.', 403


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5661)
