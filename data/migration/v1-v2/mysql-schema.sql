INSERT INTO VERSION (version, updated_by) VALUES (2, 'v1-v2 Migration');


CREATE TABLE member_traffic(
	guildid BIGINT NOT NULL,
	userid BIGINT NOT NULL,
	first_joined INT,
	last_joined INT,
	last_departure INT,
	departure_name VARCHAR(64),
	departure_nickname VARCHAR(64),
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (guildid,userid)
);

CREATE TABLE guild_join_logging(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid INT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_departure_logging(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid INT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);
