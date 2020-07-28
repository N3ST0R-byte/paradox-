CREATE TABLE users_props(
	property TEXT NOT NULL,
	shared BOOLEAN NOT NULL,
	PRIMARY KEY (property)
);

CREATE TABLE users(
	userid INTEGER NOT NULL,
	property TEXT NOT NULL,
	value TEXT,
	PRIMARY KEY (userid, property),
	FOREIGN KEY (property)
		REFERENCES users_props (property)
);

CREATE TABLE guilds_props(
	property TEXT NOT NULL,
	shared BOOLEAN NOT NULL,
	PRIMARY KEY (property)
);

CREATE TABLE guilds(
	guildid INTEGER NOT NULL,
	property TEXT NOT NULL,
	value TEXT,
	PRIMARY KEY (guildid, property),
	FOREIGN KEY (property)
		REFERENCES guilds_props (property)
);

CREATE TABLE members_props(
	property TEXT NOT NULL,
	shared BOOLEAN NOT NULL,
	PRIMARY KEY (property)
);

CREATE TABLE members(
	guildid INTEGER NOT NULL,
	userid INTEGER NOT NULL,
	property TEXT NOT NULL,
	value TEXT,
	PRIMARY KEY (guildid, userid, property),
	FOREIGN KEY (property)
		REFERENCES members_props (property)
);