import logging
import datetime as dt

from settings import GuildSetting, Boolean, RoleList, ListData, BoolData
from registry import tableInterface, schema_generator, Column, ColumnType
from logging import log

from .module import guild_admin_module as module


# TODO: Ward with admin ward
# @module.cmd('forgetuser',
#             short_help="Forget stored persistent roles for one or all users.",
#             flags=['all'])
# async def cmds_forgetuser(ctx, flags):
#     """
#     Usage``:
#         {prefix}forgetuser <userid>
#         {prefix}forgetuser --all
#     Description:
#         Forgets the persistent roles stored for a user.
#         When used with '--all', forgets all persistent roles for this guild.
#     """
#     if ctx.flags['all']:
#         # Confirm the author actually wants to do this
#         result = await ctx.ask(
#             "This will forget all stored persistent roles for this guild?")
#         if result == 0:
#             await ctx.reply("Cancelling rol")
#         else:
#             ctx.data.conn.cursor().execute("delete from members_long where serverid = {} and property = 'persistent_roles'".format(ctx.server.id))
#             ctx.data.conn.commit()
#             await ctx.reply("Persistent roles forgotten.")
#     elif ctx.arg_str:
#         # They want us to forget a single user.
#         if not ctx.arg_str.isdigit():
#             await ctx.reply("User to forget must be given by userid.")
#         else:
#             # Try and make sure the user exists
#             user = await ctx.bot.get_user_info(ctx.arg_str)
#             if user:
#                 # Forget persistent roles for this user
#                 await ctx.data.members_long.set(ctx.server.id, user.id, "persistent_roles", None)
#                 await ctx.reply("Persistent roles cleared for user `{}`!".format(ctx.arg_str))
#             else:
#                 # The user doesn't exist
#                 await ctx.reply("This user isn't known to Discord!")
#     else:
#         # Usage statement
#         await ctx.reply("Please see `{}help forgetuser` for usage!".format((await ctx.bot.get_prefixes(ctx))[0]))


# Define configuration settings

# Define configuration setting role_persistence (bool, enabled/disabled)
@module.guild_setting
class role_persistence(BoolData, Boolean, GuildSetting):
    attr_name = "role_persistence"
    category = "Moderation"

    name = "role_persistence"
    desc = "Whether roles will be given back to members who re-join."

    long_desc = ("Whether roles will be stored when a member leaves and given back when the member rejoins. "
                 "Any roles in the setting `role_persistence_ignores` will not be returned to them, "
                 "and users may be forgetten with the command `forgetmember`.")

    _outputs = {True: "Enabled",
                False: "Disabled"}

    _table_interface_name = "guild_role_persistence"


# Define configuration setting role_persistence_ignores (Role list)
@module.guild_setting
class role_persistence_ignores(ListData, RoleList, GuildSetting):
    attr_name = "role_persistence_ignores"
    category = "Moderation"

    name = "role_persistence_ignores"
    desc = "List of roles ignored by role persistence."

    long_desc = "Roles which will not be given back to a member when they rejoin, even if they had them when they left."

    _table_interface_name = "guild_role_persistence_ignores"
    _data_column = "roleid"


# Define event handlers

async def store_roles(client, member):
    """
    Store member roles when the member leaves.
    """
    # Collect a list of member roles
    role_list = [role.id for role in member.roles]

    # Don't update if the member joined in the last 10 seconds, to allow time for autoroles and role addition
    if dt.datetime.utcnow().timestamp() - member.joined_at.timestamp() < 10:
        return

    # Delete the stored roles associated to this member
    client.data.members_stored_roles.delete_where(guildid=member.guild.id, userid=member.id)

    # Insert the new roles if there are any
    if role_list:
        client.data.members_stored_roles.insert_many(
            *((member.guild.id, member.id, role.id) for role in role_list),
            insert_keys=('guildid', 'userid', 'roleid')
        )


async def restore_roles(client, member):
    """
    Restore member roles when a member rejoins.
    """
    if not client.guild_conf.role_persistence.get(client, member.guild.id).value:
        # Return if role persistence is not enabled
        return

    # Retrieve the stored roles for this member
    roleids = client.data.members_stored_roles.select_where(guildid=member.guild.id, userid=member.id)

    if roleids:
        # Get the ignored roles
        ignored = set(client.guild_conf.role_persistence_ignores.get(client, member.guild.id).value)
        # Filter the roles
        roleids = [roleid for roleid in roleids if roleid not in ignored]

    if roleids and member.guild.me.guild_permissions.manage_roles:
        # Get the associated roles, removing the nonexistent ones
        roles = [member.guild.get_role(roleid) for roleid in roleids]
        roles = [role for role in roles if role is not None]

        # Retrieve my top role with manage role permissions
        my_mr_roles = [role for role in member.guild.me.roles
                       if role.permissions.manage_roles or role.permissions.administrator]

        # Filter roles based on what I have permission to add
        if my_mr_roles:
            max_mr_role = max(my_mr_roles)
            roles = [role for role in roles if role < max_mr_role]
        else:
            roles = None

        # Add the roles if there are any left
        if roles:
            try:
                await member.add_roles(*roles, reason="Restoring member roles (Role persistence)")
            except Exception as e:
                log("Failed to restore roles for new member '{}' (uid:{}) in guild '{} (gid:{})."
                    " Exception: {}".format(member,
                                            member.id,
                                            member.guild.name,
                                            member.guild.id,
                                            e.__repr__()),
                    context="RESTORE_ROLE",
                    level=logging.WARNING)


@module.init_task
def attach_restore_roles(client):
    client.add_after_event('member_join', store_roles)
    client.add_after_event('member_leave', restore_roles)


# Define data interfaces
role_persistence_schema = schema_generator(
    "guild_role_persistence",
    Column("guildid", ColumnType.SNOWFLAKE, primary=True, required=True)
)

role_persistence_ignores_schema = schema_generator(
    "guild_role_persistence_ignores",
    Column("guildid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("roleid", ColumnType.SNOWFLAKE, primary=True, required=True)
)

member_stored_roles_schema = schema_generator(
    "member_stored_roles",
    Column("guildid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("userid", ColumnType.SNOWFLAKE, primary=True, required=True),
    Column("roleid", ColumnType.SNOWFLAKE, primary=False, required=True)
)

@module.data_init_task
def attach_rolepersistence_data(client):
    mysql_schema, sqlite_schema, columns = role_persistence_schema
    interface = tableInterface(
        client.data,
        "guild_role_persistence",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "guild_role_persistence")

    mysql_schema, sqlite_schema, columns = role_persistence_ignores_schema
    interface = tableInterface(
        client.data,
        "guild_role_persistence_ignores",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "guild_role_persistence_ignores")

    mysql_schema, sqlite_schema, columns = member_stored_roles_schema
    interface = tableInterface(
        client.data,
        "member_stored_roles",
        app=client.app,
        column_data=columns,
        shared=False,
        sqlite_schema=sqlite_schema,
        mysql_schema=mysql_schema,
    )
    client.data.attach_interface(interface, "member_stored_roles")
