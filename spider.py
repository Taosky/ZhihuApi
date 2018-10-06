# coding:utf-8
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from utils import get_article_type
from models import Author, Day, Article, Comment, ArticleAuthor
from bs4 import BeautifulSoup
from database import db_session

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 '
                  'Safari/537.36'}


async def get_json_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            result = await response.text()
            return json.loads(result)


# 添加作者到数据库
def add_author(authors):
    author_names = set()
    for author in authors:
        if author[0] in author_names:
            continue
        else:
            author_names.add(author[0])
        if Author.query.filter_by(name=author[0]).count() == 0:
            new_author = Author(name=author[0], avatar=author[1], bio=author[2])
            db_session.add(new_author)


# 添加评论到数据库
def add_comments(comments):
    comment_ids = set()
    for comment in comments:
        if comment['id'] in comment_ids:
            continue
        else:
            comment_ids.add(comment['id'])
        if Comment.query.filter_by(id=comment['id']).count() == 0:
            new_comment = Comment(id=comment['id'], author=comment['author'], type=comment['type'],
                                  article_id=comment['article_id'], content=comment['content'], likes=comment['likes'],
                                  time=comment['time'],
                                  reply_to=comment['reply_to']['id'] if 'reply_to' in comment and 'id' in comment[
                                      'reply_to'] else 0)
            db_session.add(new_comment)


# 添加文章作者对应关系到数据库
def add_article_author(article_id, article_authors):
    for one_author in article_authors:
        if ArticleAuthor.query.filter_by(article_id=article_id, author=one_author[0]).count() == 0:
            new_article_author = ArticleAuthor(article_id=article_id, author=one_author[0])
            db_session.add(new_article_author)


# 获取文章html内的信息
def get_article_authors(html):
    soup = BeautifulSoup(html, 'html.parser')
    author_names = [node.get_text().strip('，。') for node in soup.find_all('span', class_='author')]
    author_avatars = [node['src'] for node in soup.find_all('img', class_='avatar')]
    # 作者信息
    authors = [(author_names[i], author_avatars[i], '') for i in range(len(author_names))]
    return authors


# 获取评论,作者
async def get_article_comments(article_id):
    short_comments_api = 'https://news-at.zhihu.com/api/4/story/{}/short-comments'.format(article_id)
    short_comments = []
    short_comment_result = await get_json_data(short_comments_api)
    for comment in short_comment_result['comments']:
        comment['type'] = 'short'
        comment['article_id'] = article_id
        short_comments.append(comment)

    long_comments_api = 'https://news-at.zhihu.com/api/4/story/{}/long-comments'.format(article_id)
    long_comments = []
    long_comment_result = await get_json_data(long_comments_api)
    for comment in long_comment_result['comments']:
        comment['type'] = 'long'
        comment['article_id'] = article_id
        long_comments.append(comment)

    comments = short_comments + long_comments

    authors = [(comment['author'], comment['avatar'], '') for comment in comments]

    return comments, authors


async def start_article(story, date):
    print('start article {}'.format(story['id']))
    if Article.query.filter_by(id=story['id']).count() == 0:
        api_url = 'https://news-at.zhihu.com/api/4/news/{}'.format(story['id'])
        article_data = await get_json_data(api_url)
        article_authors = get_article_authors(article_data['body'])
        comments, comment_authors = await get_article_comments(story['id'])
        article_type = get_article_type(article_data['title'])

        # 文章
        new_article = Article(id=story['id'], title=article_data['title'], date=date, url=article_data['share_url'],
                              image=article_data['image'] if 'image' in article_data else '', type=article_type,
                              data=json.dumps(article_data))
        db_session.add(new_article)

        # 评论
        add_comments(comments)

        # 作者
        author_names = []
        authors = []
        for author in article_authors + comment_authors:
            if author[0] not in author_names:
                author_names.append(author[0])
                authors.append(author)

        add_author(authors)

        # 文章作者关系
        add_article_author(story['id'], article_authors)

        db_session.commit()


# 从日期开始获取
def start_before(date_before):
    # 获取日期内容
    url = 'https://news-at.zhihu.com/api/4/news/before/{}'.format(date_before)
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(get_json_data(url))
    loop.run_until_complete(task)
    json_data = task.result()
    date = json_data['date']
    day_query = Day.query.filter_by(date=date)
    # 日期内容写入数据库
    if day_query.count() == 0:
        new_day = Day(date=date, data=json.dumps(json_data), update=datetime.now())
        db_session.add(new_day)
        db_session.commit()
    else:
        day_query.update({'data': json.dumps(json_data), 'update': datetime.now()})

    # 异步抓取文章
    tasks = [start_article(story, date) for story in json_data['stories']]
    loop.run_until_complete(asyncio.wait(tasks))


def update_daily():
    print('Start update daily...')
    # 23点后更新今天的内容
    if datetime.now().hour > 23:
        date_before = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
    # 其他时间更新昨天的内容
    else:
        date_before = datetime.now().strftime('%Y%m%d')
    start_before(date_before)
    print('Finished daily update.')


if __name__ == '__main__':
    update_daily()
