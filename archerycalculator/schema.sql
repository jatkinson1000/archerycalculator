DROP TABLE IF EXISTS genders;
DROP TABLE IF EXISTS bowstyles;
DROP TABLE IF EXISTS ages;
DROP TABLE IF EXISTS rounds;
DROP TABLE IF EXISTS classes;

CREATE TABLE genders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  gender_enum TEXT NOT NULL,
  gender TEXT NOT NULL
);

CREATE TABLE bowstyles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  bowstyle_enum TEXT NOT NULL,
  bowstyle TEXT NOT NULL,
  disciplines TEXT NOT NULL
);

CREATE TABLE ages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  age_enum TEXT NOT NULL,
  age_group TEXT NOT NULL,
  gov_body TEXT NOT NULL,
  male_dist TEXT NOT NULL,
  female_dist TEXT NOT NULL,
  sighted_dist_max TEXT NOT NULL,
  sighted_dist_min TEXT NOT NULL,
  unsighted_dist_max TEXT NOT NULL,
  unsighted_dist_min TEXT NOT NULL
);

CREATE TABLE rounds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  round_name TEXT NOT NULL,
  code_name TEXT UNIQUE NOT NULL,
  location TEXT,
  body TEXT NOT NULL,
  family TEXT NOT NULL
);

CREATE TABLE classes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  shortname TEXT NOT NULL,
  longname TEXT NOT NULL,
  location TEXT NOT NULL
);
