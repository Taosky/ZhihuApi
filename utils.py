# coding:utf-8
from datetime import datetime, timedelta

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 '
                  'Safari/537.36'}


def get_before_date(date):
    return (parse_ymd(date) + timedelta(days=1)).strftime('%Y%m%d')


def parse_ymd(s):
    year_s, mon_s, day_s = s[:4], s[4:6], s[6:8]
    return datetime(int(year_s), int(mon_s), int(day_s))


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
