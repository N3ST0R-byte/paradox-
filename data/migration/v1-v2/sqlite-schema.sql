INSERT INTO VERSION (version, updated_by) VALUES (2, 'v1-v2 Migration');

CREATE TABLE guild_starboards(
	app TEXT NOT NULL,
	guildid INTEGER NOT NULL,
	channelid INTEGER,
	emoji TEXT,
	threshold INTEGER NOT NULL DEFAULT 1,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_starboard_roles(
	app TEXT NOT NULL,
	guildid INTEGER NOT NULL,
	roleid INTEGER NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE message_stars(
	app TEXT NOT NULL,
	msgid INTEGER NOT NULL,
	starmsgid INTEGER NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (app,msgid)
);
