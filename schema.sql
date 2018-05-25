drop table if exists day_date;
create table day (
  id integer primary key autoincrement,
  date text not null,
  stories text not null
);
create table article (
  id integer primary key autoincrement,
  article_id integer,
  data text not null
);
create table day_top (
  id integer primary key autoincrement,
  date text not null,
  stories text not null
);
