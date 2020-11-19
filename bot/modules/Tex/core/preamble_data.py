from registry import schema_generator, Column, ColumnType, tableInterface

from ..module import latex_module as module


# The active user and guild preambles
user_preamble_schemas = schema_generator(
    "user_latex_preambles",
    Column('userid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('preamble', ColumnType.TEXT, primary=False, required=False),
    Column('previous_preamble', ColumnType.TEXT, primary=False, required=False),
    Column('whitelisted', ColumnType.BOOL, primary=False, required=False),
)

guild_preamble_schemas = schema_generator(
    "guild_latex_preambles",
    Column('guildid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('preamble', ColumnType.TEXT, primary=False, required=True),
)

# The pending preambles
user_pending_preamble_schemas = schema_generator(
    "user_pending_preambles",
    Column('userid', ColumnType.SNOWFLAKE, primary=True, required=True),
    Column('app', ColumnType.SHORTSTRING, required=True),
    Column('username', ColumnType.SHORTSTRING, required=True),
    Column('pending_preamble', ColumnType.TEXT, required=True),
    Column('pending_preamble_diff', ColumnType.TEXT, required=False),
    Column('submission_time', ColumnType.INT, required=True),
    Column('submission_message_id', ColumnType.SNOWFLAKE, required=False),
    Column('submission_summary', ColumnType.MSGSTRING, required=True),
    Column('submission_source_id', ColumnType.SNOWFLAKE, required=True),
    Column('submission_source_name', ColumnType.SHORTSTRING, required=True),
)

# Global data
global_preset_schemas = schema_generator(
    "global_latex_presets",
    Column('name', ColumnType.SHORTSTRING, required=True),
    Column('preset', ColumnType.TEXT, required=True),
)

global_whitelist_schemas = schema_generator(
    "global_latex_package_whitelist",
    Column('package', ColumnType.SHORTSTRING, required=True),
)


# Attach data interfaces
@module.data_init_task
def attach_preamble_data(client):
    # User active preambles
    mysql_schema, sqlite_schema, columns = user_preamble_schemas
    interface = tableInterface(
        client.data,
        "user_latex_preambles",
        app=client.app,
        column_data=columns,
        shared=True,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "user_latex_preambles")

    # Guild active preambles
    mysql_schema, sqlite_schema, columns = guild_preamble_schemas
    interface = tableInterface(
        client.data,
        "guild_latex_preambles",
        app=client.app,
        column_data=columns,
        shared=True,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "guild_latex_preambles")

    # User pending preambles
    mysql_schema, sqlite_schema, columns = user_pending_preamble_schemas
    interface = tableInterface(
        client.data,
        "user_pending_preambles",
        app=client.app,
        column_data=columns,
        shared=True,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "user_pending_preambles")

    # Global presets
    mysql_schema, sqlite_schema, columns = global_preset_schemas
    interface = tableInterface(
        client.data,
        "global_latex_presets",
        app=client.app,
        column_data=columns,
        shared=True,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "global_latex_presets")

    # Global package whitelist
    mysql_schema, sqlite_schema, columns = global_whitelist_schemas
    interface = tableInterface(
        client.data,
        "global_package_whitelist",
        app=client.app,
        column_data=columns,
        shared=True,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "global_package_whitelist")
