# coding:utf-8
from datetime import datetime
import requests
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 '
                  'Safari/537.36'}


def parse_ymd(s):
    year_s, mon_s, day_s = s[:4], s[4:6], s[6:8]
    return datetime(int(year_s), int(mon_s), int(day_s))


def replace_unsafe_img(text):
    return text.replace('http:\\/\\/pic', 'https:\\/\\/pic')


def get_json_data(url):
    r = requests.get(url, headers=HEADERS)
    text = replace_unsafe_img(r.text)
    return json.loads(text)


def get_article_type(title):
    if '瞎扯 ·' in title:
        a_type = 'xiache'
    elif '大误 ·' in title:
        a_type = 'dawu'
    elif '小事 ·' in title:
        a_type = 'xiaoshi'
    else:
        a_type = 'normal'
    return a_type
