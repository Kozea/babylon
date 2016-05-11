drop table if exists users;
create table users (
  id_user integer primary key autoincrement,
  surname text not null,
  name text not null,
  nickname text,
  ranking integer,
  photo text,
  numberMatchs integer
);

drop table if exists matchs;
create table matchs (
  id_match integer primary key autoincrement,
  date date ,
  score_e1 integer,
  score_e2 integer,
  id_team1 integer,
  id_team2 integer,
  FOREIGN KEY(id_team1) REFERENCES teams(id_team),
  FOREIGN KEY(id_team2) REFERENCES teams(id_team)
  
);

drop table if exists teams;
create table teams (
  id_team integer primary key autoincrement,
  id_player1 integer not null,
  id_player2 integer,
  name text,
  FOREIGN KEY(id_player1) REFERENCES users(id_user),
  FOREIGN KEY(id_player2) REFERENCES users(id_user)
);