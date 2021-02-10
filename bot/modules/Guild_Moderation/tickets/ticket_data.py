from registry import tableInterface, Column, ColumnType, tableSchema, ForeignKey, ReferenceAction

from ..module import guild_moderation_module as module

from . import TimedMuteTicket, UnmuteTicket  # noqa

# Define data schemas
ticket_schema = tableSchema(
    "guild_moderation_tickets",
    Column('ticketid', ColumnType.INT, autoincrement=True, primary=True),
    Column('ticket_type', ColumnType.INT, required=True),
    Column('guildid', ColumnType.SNOWFLAKE, required=True),
    Column('modid', ColumnType.SNOWFLAKE, required=True),
    Column('agentid', ColumnType.SNOWFLAKE, required=True),
    Column('app', ColumnType.SHORTSTRING, required=True),
    Column('msgid', ColumnType.SNOWFLAKE, required=False),
    Column('auditid', ColumnType.SNOWFLAKE, required=False),
    Column('reason', ColumnType.MSGSTRING, required=False),
    Column('created_at', ColumnType.INT, required=True),
)

member_schema = tableSchema(
    "guild_moderation_ticket_members",
    Column('ticketid', ColumnType.INT, required=True),
    Column('memberid', ColumnType.SNOWFLAKE, required=True),
    ForeignKey('ticketid', ticket_schema.name, 'ticketid', on_delete=ReferenceAction.CASCADE)
)

combined_raw_schema = """\
CREATE VIEW
    guild_moderation_tickets_combined
AS
SELECT
    t.ticketid AS ticketid,
    t.ticket_type AS ticket_type,
    t.guildid AS guildid,
    t.modid AS modid,
    t.agentid AS agentid,
    t.app AS app,
    t.msgid AS msgid,
    t.auditid AS auditid,
    t.reason AS reason,
    t.created_at AS created_at,
    row_number() OVER (PARTITION BY t.guildid ORDER BY t.ticketid) AS ticketgid,
    timedmutes.duration AS tmute_duration,
    timedmutes.roleid AS tmute_roleid,
    timedmutes.unmute_timestamp AS tmute_unmute_timestamp
FROM
    guild_moderation_tickets t
LEFT JOIN guild_timed_mute_tickets timedmutes ON t.ticketid = timedmutes.ticketid;
"""
combined_columns = (
    *ticket_schema.interface_columns,
    ('ticketgid', int),
    ('tmute_duration', int),
    ('tmute_roleid', int),
    ('tmute_unmute_timestamp', int)
)


# Attach data interfaces
@module.data_init_task
def attach_mod_ticket_data(client):
    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, ticket_schema, shared=True),
        "guild_mod_tickets"
    )

    client.data.attach_interface(
        tableInterface(
            client.data,
            "guild_moderation_tickets_combined",
            client.app,
            combined_columns,
            mysql_schema=combined_raw_schema,
            sqlite_schema=combined_raw_schema
        ),
        "guild_mod_tickets_combined"
    )

    client.data.attach_interface(
        tableInterface.from_schema(client.data, client.app, member_schema, shared=True),
        "guild_mod_ticket_members"
    )
