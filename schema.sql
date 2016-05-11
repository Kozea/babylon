drop table if exists users;
create table users (
  id_user integer primary key autoincrement,
  surname text not null,
  name text not null,
  nickname text,
  photo text
);

drop table if exists matchs;
create table matchs (
  id_match integer primary key autoincrement,
  date date ,
  score_e1 integer,
  score_e2 integer,
  id_player11 integer not null,
  id_player12 integer,
  id_player21 integer not null,
  id_player22 integer,
  FOREIGN KEY(id_player11) REFERENCES users(id_user),
  FOREIGN KEY(id_player12) REFERENCES users(id_user),
  FOREIGN KEY(id_player21) REFERENCES users(id_user),
  FOREIGN KEY(id_player22) REFERENCES users(id_user)
  
);

