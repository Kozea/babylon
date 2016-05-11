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

-- Users
-- ~ INSERT INTO users VALUES (0, 'Michel', 'Guy', 'Peupeul', 1,'photo0');
-- ~ INSERT INTO users VALUES (1, 'Gripay', 'Yann', 'Cocaine', 2, 'photo1');
-- ~ INSERT INTO users VALUES (2, 'Guégan', 'Thomas', 'Barbiche', 3, 'photo2');
-- ~ INSERT INTO users VALUES (3, 'Lepeigneux', 'Estelle', 'La Malgache', 4, 'photo3');

-- teams
-- ~ INSERT INTO teams VALUES (0, 1, NULL, NULL);
-- ~ INSERT INTO teams VALUES (1, 2, NULL, NULL);
-- ~ INSERT INTO teams VALUES (2, 2, 1, 'La team 1');
-- ~ INSERT INTO teams VALUES (3, 3, 0, 'Los Rodrigos Fuerte');

-- Matchs
-- ~ INSERT INTO matchs VALUES (0, "2010-12-30 12:10:04.100", 10, 9, 0, 1);
-- ~ INSERT INTO matchs VALUES (1, "2010-12-30 12:11:04.100", 1, 10, 2, 3);
