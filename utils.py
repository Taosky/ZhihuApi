from datetime import datetime


def parse_ymd(s):
    year_s, mon_s, day_s = s[:4], s[4:6], s[6:8]
    return datetime(int(year_s), int(mon_s), int(day_s))


def replace_unsafe_img(text):
    text.replace('http://pic', 'https://pic')
