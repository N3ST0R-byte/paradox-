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

CREATE TABLE guild_autoroles(
	guildid INTEGER NOT NULL,
	roleid INTEGER NOT NULL,
	PRIMARY KEY (guildid,roleid)
);

CREATE TABLE guild_bot_autoroles(
	guildid INTEGER NOT NULL,
	roleid INTEGER NOT NULL,
	PRIMARY KEY (guildid,roleid)
);

CREATE TABLE guild_greetings(
	guildid INTEGER NOT NULL,
	channelid INTEGER,
	message TEXT,
	PRIMARY KEY (guildid)
);

CREATE TABLE guild_farewells(
	guildid INTEGER NOT NULL,
	channelid INTEGER,
	message TEXT,
	PRIMARY KEY (guildid)
);

CREATE TABLE guild_disabled_channels(
	guildid INTEGER NOT NULL,
	channelid INTEGER NOT NULL,
	PRIMARY KEY (guildid,channelid)
);

CREATE TABLE guild_cleaned_channels(
	guildid INTEGER NOT NULL,
	channelid INTEGER NOT NULL,
	delay INTEGER NOT NULL DEFAULT 60,
	PRIMARY KEY (guildid,channelid)
);

CREATE TABLE guild_role_persistence(
	guildid INTEGER NOT NULL,
	PRIMARY KEY (guildid)
);

CREATE TABLE guild_role_persistence_ignores(
	guildid INTEGER NOT NULL,
	roleid INTEGER NOT NULL,
	PRIMARY KEY (guildid,roleid)
);

CREATE TABLE member_stored_roles(
	guildid INTEGER NOT NULL,
	userid INTEGER NOT NULL,
	roleid INTEGER NOT NULL,
	PRIMARY KEY (guildid,userid)
);