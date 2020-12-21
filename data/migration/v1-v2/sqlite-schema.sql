INSERT INTO VERSION (version, updated_by) VALUES (2, 'v1-v2 Migration');


CREATE TABLE member_traffic(
	guildid INTEGER NOT NULL,
	userid INTEGER NOT NULL,
	first_joined INTEGER,
	last_joined INTEGER,
	last_departure INTEGER,
	departure_name TEXT,
	departure_nickname TEXT,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (guildid,userid)
);

CREATE TABLE guild_logging_joins(
	app TEXT NOT NULL,
	guildid INTEGER NOT NULL,
	channelid INTEGER NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_logging_departures(
	app TEXT NOT NULL,
	guildid INTEGER NOT NULL,
	channelid INTEGER NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);
