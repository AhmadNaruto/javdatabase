create table if not exists video (
  id integer primary key,
  title text,
  series integer,
  studio integer,
  label integer,
  director integer,
  dvd_id text,
  content_id text,
  release text,
  duration text,
  thumbnail text,
  foreign key (series) references series (id),
  foreign key (studio) references studio (id),
  foreign key (label) references label (id),
  foreign key (director) references director (id)
);
create table if not exists actres (
  id integer primary key,
  name text,
  thumbnail text,
  about text,
  unique(name)
);
create table if not exists studio (id integer primary key, name text, unique(name));
create table if not exists series (id integer primary key, name text, unique(name));
create table if not exists label (id integer primary key, name text, unique(name));
create table if not exists director (id integer primary key, name text, unique(name));
create table if not exists genre (id integer primary key, name text, unique(name));
create table if not exists rf_genre (
  id integer primary key,
  vid integer,
  gid integer,
  foreign key (vid) references video (id),
  foreign key (gid) references genre (id)
);
create table if not exists rf_actres (
  id integer primary key,
  vid integer,
  aid integer,
  foreign key (vid) references video (id),
  foreign key (aid) references actres (id)
);
