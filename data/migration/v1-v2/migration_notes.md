# Migration from v1 to v2
Continuing the migration from the `key-value` property tables to individual data tables.

This version migrates the following features:
* Guild logging

# Migration operation
Apply the `mysql-schema.sql` or `sqlite-schema.sql` script to the database, as required.
The `sqlite` migration script does not migrate the old data, only updating the version and creating the new tables.


# Description of each of the properties in the v0 property tables, and subsequent action
Unless explicitly stated, value data is encoded by `json.dumps()` and may be reloaded into the actual values described below by `json.loads()`.

## `servers` table
* `joinlog_ch`
    * Property name: `joinlog_ch`
    * Application: `paradox`
    * Type: `str` or literal `null`
    * Description: The channel to send user join information messages
    * Migration note: The `joinlog` setting is splitting into two, `joinlog` and `departurelog`.
    * Parse as: `id`
    * Action
        * Target tables: `[guild_logging_joins, guild_logging_departures]`
        * Insert type: `insert`
        * Insert keymap: `{'guildid': 'row.serverid', 'channelid': 'row.value', 'app': 'paradox'}`

* `texit_joinlog_ch`
    * Property name: `joinlog_ch`
    * Application: `texit`
    * Type: `str` or literal `null`
    * Description: The channel to send user join information messages
    * Migration note: The `joinlog` setting is splitting into two, `joinlog` and `departurelog`.
    * Parse as: `id`
    * Action
        * Target tables: `[guild_logging_joins, guild_logging_departures]`
        * Insert type: `insert`
        * Insert keymap: `{'guildid': 'row.serverid', 'channelid': 'row.value', 'app': 'texit'}`

* `userlog_ch`
    * Property name: `userlog_ch`
    * Application: `paradox`
    * Type: `str` or literal `null`
    * Description: The id of the user event log
    * Parse as: `id`
    * Action
        * Target table: `guild_userupdate_channel`
        * Insert type: `insert`
        * Insert keymap: `{'guildid': 'row.serverid', 'channelid': 'row.value', 'app': 'paradox'}`

* `texit_userlog_ch`
    * Property name: `userlog_ch`
    * Application: `texit`
    * Type: `str` or literal `null`
    * Description: The id of the user event log
    * Parse as: `id`
    * Action
        * Target table: `guild_userupdate_channel`
        * Insert type: `insert`
        * Insert keymap: `{'guildid': 'row.serverid', 'channelid': 'row.value', 'app': 'texit'}`

* `userlog_events`
    * Property name: `userlog_events`
    * Application: `paradox`
    * Type: `List[str]`
    * Description: The list of events to log in the user event log
    * Parse as: `string list`
    * Action
        * Not to be migrated

* `texit_userlog_events`
    * Property name: `userlog_events`
    * Application: `texit`
    * Type: `List[str]`
    * Description: The list of events to log in the user event log
    * Parse as: `string list`
    * Action
        * Not to be migrated

* `userlog_ignore`
    * Property name: `userlog_ignore`
    * Application: `paradox`
    * Type: `List[str]` or literal `null`
    * Description: The list of user ids to ignore in the user event log
    * Parse as: `id list`
    * Action
        * Not to be migrated

* `texit_userlog_ignore`
    * Property name: `userlog_ignore`
    * Application: `texit`
    * Type: `List[str]` or literal `null`
    * Description: The list of user ids to ignore in the user event log
    * Parse as: `id list`
    * Action
        * Not to be migrated
