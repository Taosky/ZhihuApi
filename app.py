# coding:utf-8
from flask import Flask, request
from flask_cors import CORS

from sqlalchemy import desc, func
from database import db_session
from models import Author, Day, Article, Comment, ArticleAuthor

from spider import start_before
from utils import get_before_date
import json

app = Flask(__name__)
CORS(app)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def index():
    return 'Forbidden', 403


@app.route('/v1')
def v1():
    return 'Version 1'


@app.route('/v1/day/<date>')
def show_day(date):
    # 不存在运行爬虫
    if Day.query.filter_by(date=date).count() == 0:
        before_date = get_before_date(date)
        start_before(before_date)
    return Day.query.filter_by(date=date).first().data


@app.route('/v1/article/<a_id>')
def show_article(a_id):
    return Article.query.filter_by(id=a_id).first().data


@app.route('/v1/author/<name>')
def show_author(name):
    author = Author.query.filter_by(name=name).first()
    author_dict = author.__dict__
    del author_dict['_sa_instance_state']
    return json.dumps(author_dict)


@app.route('/v1/comment/<int:c_id>')
def show_comment(c_id):
    comment = Comment.query.filter_by(id=c_id).first()
    comment_dict = comment.__dict__
    del comment_dict['_sa_instance_state']
    return json.dumps(comment_dict)


@app.route('/v1/article/search', methods=['POST'])
def search_article():
    args = request.get_json()
    keyword = args['query'] if 'query' in args else ''
    like_str = '%{}%'.format(keyword)
    author = args['author'] if 'author' in args else ''
    a_type = args['type'] if 'type' in args else ''
    order_by = Article.type if 'order_by' in args and args['order_by'] == 'type' else Article.date
    # start_time = args['start_time'] if 'start_time' in args else ''
    # end_time = args['end_time'] if 'end_time' in args else ''
    page = args['page'] if 'page' in args else 1
    page_size = 15

    if author:
        query_request = Article.query.join(ArticleAuthor, Article.id == ArticleAuthor.article_id).filter(
            ArticleAuthor.author == author, Article.title.contains(like_str))
        total_query = db_session.query(func.count(Article.id)).join(ArticleAuthor,
                                                                    Article.id == ArticleAuthor.article_id).filter(
            ArticleAuthor.author == author, Article.title.contains(like_str))
    else:
        query_request = Article.query.filter(Article.title.contains(like_str))
        total_query = db_session.query(func.count(Article.id)).filter(Article.title.contains(like_str))
    if a_type:
        query_request = query_request.filter(Article.type == a_type)
        total_query = total_query.filter(Article.type == a_type)
    # 排序分页

    total = total_query.first()[0]

    result = {'articles': [], 'total': total, 'page': page, 'page_size': page_size}
    for article in query_request.order_by(desc(order_by)).offset((page - 1) * page_size).limit(page_size):
        article_dict = article.__dict__
        article_dict['authors'] = [one.author for one in
                                   ArticleAuthor.query.filter(ArticleAuthor.article_id == article_dict['id'])]
        del article_dict['_sa_instance_state']
        result['articles'].append(article_dict)
    return json.dumps(result)


@app.route('/v1/comment/search', methods=['POST'])
def search_comment():
    args = request.get_json()
    a_id = int(args['article_id']) if 'article_id' in args else ''
    author = args['author'] if 'author' in args else ''
    c_type = args['type'] if 'type' in args else ''
    order_by = Comment.time if 'order_by' in args and args['order_by'] == 'time' else Comment.likes
    page = args['page'] if 'page' in args else 1
    page_size = 20

    query_request = Comment.query
    if a_id:
        query_request = query_request.filter(Comment.article_id == a_id)
    if author:
        query_request = query_request.filter(Comment.author == author)
    if c_type:
        query_request = query_request.filter(Comment.type == c_type)

    result = {'comments': [], 'total': query_request.count(), 'page': page, 'page_size': page_size}
    for comment in query_request.order_by(desc(order_by)).offset((page - 1) * page_size).limit(page_size):
        comment_dict = comment.__dict__
        del comment_dict['_sa_instance_state']
        comment_dict['avatar'] = Author.query.filter(Author.name == comment_dict['author']).first().avatar
        result['comments'].append(comment_dict)
    return json.dumps(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5661)
