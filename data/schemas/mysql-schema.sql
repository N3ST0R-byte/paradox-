CREATE TABLE VERSION(
	version INT NOT NULL,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_by VARCHAR(64),
	PRIMARY KEY (version)
);
INSERT INTO VERSION (version, updated_by) VALUES (1, 'Initial Creation');

CREATE TABLE admin_snippets(
	name VARCHAR(64) NOT NULL,
	author BIGINT NOT NULL,
	description VARCHAR(2048) NOT NULL,
	content TEXT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (name)
);

CREATE TABLE admin_user_blacklist(
	userid BIGINT NOT NULL,
	added_by BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (userid)
);

CREATE TABLE user_prefixes(
	app VARCHAR(64) NOT NULL,
	userid BIGINT NOT NULL,
	prefix VARCHAR(64) NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,userid)
);

CREATE TABLE user_latex_preambles(
	userid BIGINT NOT NULL,
	preamble TEXT,
	previous_preamble TEXT,
	whitelisted BOOLEAN,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (userid)
);

CREATE TABLE guild_latex_preambles(
	guildid BIGINT NOT NULL,
	preamble TEXT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (guildid)
);

CREATE TABLE user_pending_preambles(
	userid BIGINT NOT NULL,
	app VARCHAR(64) NOT NULL,
	username VARCHAR(64) NOT NULL,
	pending_preamble TEXT NOT NULL,
	pending_preamble_diff TEXT,
	submission_time INT NOT NULL,
	submission_message_id BIGINT,
	submission_summary VARCHAR(2048) NOT NULL,
	submission_source_id BIGINT NOT NULL,
	submission_source_name VARCHAR(64) NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (userid)
);

CREATE TABLE global_latex_presets(
	name VARCHAR(64) NOT NULL,
	preset TEXT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE global_latex_package_whitelist(
	package VARCHAR(64) NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE guild_latex_config(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	autotex BOOLEAN,
	autotex_level INT,
	require_codeblocks BOOLEAN,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_latex_channels(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid,channelid)
);

CREATE TABLE user_latex_config(
	app VARCHAR(64) NOT NULL,
	userid BIGINT NOT NULL,
	autotex BOOLEAN,
	keepsourcefor INT,
	colour VARCHAR(64),
	alwaysmath BOOLEAN,
	alwayswide BOOLEAN,
	namestyle INT,
	autotex_level INT,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,userid)
);

CREATE TABLE guild_wolfram_appid(
	guildid BIGINT NOT NULL,
	appid VARCHAR(64),
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (guildid)
);

CREATE TABLE user_time_settings(
	userid BIGINT NOT NULL,
	timezone VARCHAR(64),
	brief_display BOOLEAN DEFAULT False,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (userid)
);

CREATE TABLE guild_selfroles(
	guildid BIGINT NOT NULL,
	roleid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (guildid,roleid)
);

CREATE TABLE guild_modroles(
	guildid BIGINT NOT NULL,
	roleid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (guildid)
);

CREATE TABLE guild_muteroles(
	guildid BIGINT NOT NULL,
	roleid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (guildid)
);

CREATE TABLE guild_autoroles(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	roleid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid,roleid)
);

CREATE TABLE guild_bot_autoroles(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	roleid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid,roleid)
);

CREATE TABLE guild_greetings(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid BIGINT,
	message TEXT,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_farewells(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid BIGINT,
	message TEXT,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_disabled_channels(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid,channelid)
);

CREATE TABLE guild_cleaned_channels(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid BIGINT NOT NULL,
	delay INT NOT NULL DEFAULT 60,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid,channelid)
);

CREATE TABLE guild_role_persistence(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_role_persistence_ignores(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	roleid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid,roleid)
);

CREATE TABLE member_stored_roles(
	guildid BIGINT NOT NULL,
	userid BIGINT NOT NULL,
	roleid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (guildid,userid,roleid)
);

CREATE TABLE guild_prefixes(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	prefix VARCHAR(64),
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_disabled_commands(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	command_name VARCHAR(64) NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid,command_name)
);