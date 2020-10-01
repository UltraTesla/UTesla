CREATE TABLE IF NOT EXISTS UTesla.users (
  id int unsigned NOT NULL AUTO_INCREMENT,
  user varchar(45) unique NOT NULL,
  password varchar(125) NOT NULL,
  token_limit int(10) default 1 NOT NULL,
  user_hash char(56) NOT NULL,
  guest_user bool default 0 NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS UTesla.tokens (
  id_token int unsigned NOT NULL AUTO_INCREMENT,
  id_user int unsigned NOT NULL,
  token char(64) unique NOT NULL,
  expire int NOT NULL,
  services varchar(255) NOT NULL,
  PRIMARY KEY (id_token),
  FOREIGN KEY (id_user) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS UTesla.networks (
  id_network int unsigned NOT NULL AUTO_INCREMENT,
  network varchar(68) unique NOT NULL,
  token char(64) NOT NULL,
  user varchar(45) NOT NULL,
  PRIMARY KEY (id_network)

);

CREATE TABLE IF NOT EXISTS UTesla.services (
  id_service int unsigned NOT NULL AUTO_INCREMENT,
  id_network int unsigned NOT NULL,
  service varchar(255) NOT NULL,
  priority int(10) default 0 NOT NULL,
  PRIMARY KEY (id_service),
  FOREIGN KEY (id_network) REFERENCES networks (id_network) ON DELETE CASCADE ON UPDATE CASCADE

);
