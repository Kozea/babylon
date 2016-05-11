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

insert into users values(0,"bonfante","nicolas","michel","photo");
insert into users values(1,"lepeigneux","estelle","michel","photo");
insert into users values(2,"guegan","thomas","michel","photo");

insert into matchs values(0,"2012-01-01",12,1,0,null,1,null);
insert into matchs values(1,"2012-01-01",12,1,0,null,2,null);
insert into matchs values(2,"2012-01-01",12,1,2,null,0,null);
insert into matchs values(3,"2012-01-01",12,1,2,null,0,null);
insert into matchs values(4,"2012-01-01",12,1,2,null,0,null);