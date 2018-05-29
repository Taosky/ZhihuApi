drop table if exists day_date;
create table day (
  id integer primary key autoincrement,
  date text not null UNIQUE,
  data text not null
);
create table article (
  id integer primary key autoincrement,
  article_id integer UNIQUE,
  data text not null
);
