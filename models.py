from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from database import Base


class Day(Base):
    __tablename__ = 'day'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(MEDIUMTEXT)
    date = Column(String(10), unique=True)
    update = Column(DateTime)


class Article(Base):
    __tablename__ = 'article'
    id = Column(BigInteger, primary_key=True)
    date = Column(String(10))
    title = Column(String(2000))
    url = Column(String(2000))
    image = Column(String(2000))
    data = Column(MEDIUMTEXT)
    type = Column(String(10))


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(BigInteger, primary_key=True)
    author = Column(String(100))
    content = Column(MEDIUMTEXT)
    likes = Column(Integer)
    time = Column(BigInteger)
    reply_to = Column(BigInteger)


class Author(Base):
    __tablename__ = 'author'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True)
    bio = Column(String(2000))
    avatar = Column(String(2000))


class ArticleAuthor(Base):
    __tablename__ = 'article_author'
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(BigInteger)
    author = Column(String(100))
