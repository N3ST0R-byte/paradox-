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

CREATE TABLE guild_logging_joins(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_logging_departures(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);


INSERT INTO guild_logging_joins
    (app, guildid, channelid)
SELECT
    'paradox' AS app,
    servers.serverid as guildid,
    CONVERT(JSON_UNQUOTE(servers.value), UNSIGNED INTEGER) AS channelid
FROM servers
WHERE
    servers.property = 'joinlog_ch'
    AND servers.value != 'null';

INSERT INTO guild_logging_joins
    (app, guildid, channelid)
SELECT
    'texit' AS app,
    servers.serverid as guildid,
    CONVERT(JSON_UNQUOTE(servers.value), UNSIGNED INTEGER) AS channelid
FROM servers
WHERE
    servers.property = 'texit_joinlog_ch'
    AND servers.value != 'null';

INSERT INTO guild_logging_departures
    (app, guildid, channelid)
SELECT
    'paradox' AS app,
    servers.serverid as guildid,
    CONVERT(JSON_UNQUOTE(servers.value), UNSIGNED INTEGER) AS channelid
FROM servers
WHERE
    servers.property = 'joinlog_ch'
    AND servers.value != 'null';

INSERT INTO guild_logging_departures
    (app, guildid, channelid)
SELECT
    'texit' AS app,
    servers.serverid as guildid,
    CONVERT(JSON_UNQUOTE(servers.value), UNSIGNED INTEGER) AS channelid
FROM servers
WHERE
    servers.property = 'texit_joinlog_ch'
    AND servers.value != 'null';


CREATE TABLE guild_userupdate_channel(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid BIGINT,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_userupdate_events(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	event INT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid,event)
);

CREATE TABLE guild_userupdate_ignores(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	userid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid,userid)
);


INSERT INTO guild_userupdate_channel
    (app, guildid, channelid)
SELECT
    'paradox' AS app,
    servers.serverid as guildid,
    CONVERT(JSON_UNQUOTE(servers.value), UNSIGNED INTEGER) AS channelid
FROM servers
WHERE
    servers.property = 'userlog_ch'
    AND servers.value != 'null';

INSERT INTO guild_userupdate_channel
    (app, guildid, channelid)
SELECT
    'texit' AS app,
    servers.serverid as guildid,
    CONVERT(JSON_UNQUOTE(servers.value), UNSIGNED INTEGER) AS channelid
FROM servers
WHERE
    servers.property = 'texit_userlog_ch'
    AND servers.value != 'null';
