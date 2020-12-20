INSERT INTO VERSION (version, updated_by) VALUES (2, 'v1-v2 Migration');

CREATE TABLE guild_starboards(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	channelid BIGINT,
	emoji VARCHAR(64),
	threshold INT NOT NULL DEFAULT 1,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE guild_starboard_roles(
	app VARCHAR(64) NOT NULL,
	guildid BIGINT NOT NULL,
	roleid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,guildid)
);

CREATE TABLE message_stars(
	app VARCHAR(64) NOT NULL,
	msgid BIGINT NOT NULL,
	starmsgid BIGINT NOT NULL,
	_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (app,msgid)
);


INSERT INTO guild_starboards
    (app, guildid, channelid, threshold, emoji)
SELECT
    'paradox' AS app,
    servers.serverid AS guildid,
    IF((servers_enabled.value IS NULL) OR (servers_enabled.value='true'), CONVERT(JSON_UNQUOTE(servers_channel.value), UNSIGNED INTEGER), NULL) AS channelid,
    IFNULL(servers_threshold.value, 1) AS threshold,
    JSON_UNQUOTE(servers_emoji.value) AS emoji
FROM (SELECT DISTINCT(serverid) from servers) AS servers
    LEFT JOIN servers as servers_channel ON servers.serverid = servers_channel.serverid AND servers_channel.property = "starboard_channel" AND servers_channel.value NOT IN ("0", "null")
    LEFT JOIN servers AS servers_threshold ON servers.serverid = servers_threshold.serverid AND servers_threshold.property = "starboard_threshold" AND servers_threshold.value NOT IN ("0", "null")
    LEFT JOIN servers AS servers_emoji ON servers.serverid = servers_emoji.serverid AND servers_emoji.property = "starboard_emoji" AND servers_emoji.value NOT IN ("0", "null")
    LEFT JOIN servers AS servers_enabled ON servers.serverid = servers_enabled.serverid AND servers_enabled.property = "starboard_enabled"
WHERE
    servers_channel.value IS NOT NULL
    OR servers_threshold.value IS NOT NULL
    OR servers_emoji.value IS NOT NULL;

INSERT INTO guild_starboards
    (app, guildid, channelid, threshold, emoji)
SELECT
    'texit' AS app,
    servers.serverid AS guildid,
    IF((servers_enabled.value IS NULL) OR (servers_enabled.value='true'), CONVERT(JSON_UNQUOTE(servers_channel.value), UNSIGNED INTEGER), NULL) AS channelid,
    IFNULL(servers_threshold.value, 1) AS threshold,
    JSON_UNQUOTE(servers_emoji.value) AS emoji
FROM (SELECT DISTINCT(serverid) from servers) AS servers
    LEFT JOIN servers as servers_channel ON servers.serverid = servers_channel.serverid AND servers_channel.property = "texit_starboard_channel" AND servers_channel.value NOT IN ("0", "null")
    LEFT JOIN servers AS servers_threshold ON servers.serverid = servers_threshold.serverid AND servers_threshold.property = "starboard_threshold" AND servers_threshold.value NOT IN ("0", "null")
    LEFT JOIN servers AS servers_emoji ON servers.serverid = servers_emoji.serverid AND servers_emoji.property = "texit_starboard_emoji" AND servers_emoji.value NOT IN ("0", "null")
    LEFT JOIN servers AS servers_enabled ON servers.serverid = servers_enabled.serverid AND servers_enabled.property = "texit_starboard_enabled"
WHERE
    servers_channel.value IS NOT NULL
    OR servers_threshold.value IS NOT NULL
    OR servers_emoji.value IS NOT NULL;

