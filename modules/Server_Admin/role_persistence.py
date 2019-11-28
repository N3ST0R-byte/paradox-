import discord

from paraCH import paraCH

cmds = paraCH()

"""
Handlers for role persistence, saving user roles upon leaving, and restoring on rejoin.

Handlers:
    store_roles:
        Triggers on member leaving
        Stores roles into a list of persistent roles
    recall_roles:
        Triggers on member joining
        Restores member's stored roles if possible

Member data:
    persistent_roles: int[]
        (app independent, automatic)
        Roles the member had when they last left the server.

Server data:
    role_persistence: bool
        (app independent, admin configured)
        Whether stored roles should be restored on member join.
"""


@cmds.cmd('forgetuser',
          category='Server Admin',
          short_help="Forget persistent roles for one or all users",
          flags=['all'])
@cmds.require("in_server")
@cmds.require('has_manage_server')
async def cmds_forgetuser(ctx):
    """
    Usage:
        {prefix}forgetuser <userid>
        {prefix}forgetuser --all
    Description:
        Forgets the persistent roles stored for a user.
        When used with '--all', forgets all persistent roles for the server.
    """
    if ctx.flags['all']:
        # Confirm the executor actually wants to do this
        result = await ctx.ask("Are you sure you want to forget all previous user roles for this server?")
        if result is None:
            await ctx.reply("Question timed out, aborting.")
        elif result == 0:
            await ctx.reply("Aborting...")
        else:
            ctx.data.conn.cursor().execute("delete from members_long where serverid = {} and property = 'persistent_roles'".format(ctx.server.id))
            ctx.data.conn.commit()
            await ctx.reply("Persistent roles forgotten.")
    elif ctx.arg_str:
        # They want us to forget a single user.
        if not ctx.arg_str.isdigit():
            await ctx.reply("User to forget must be given by userid.")
        else:
            # Try and make sure the user exists
            user = await ctx.bot.get_user_info(ctx.arg_str)
            if user:
                # Forget persistent roles for this user
                await ctx.data.members_long.set(ctx.server.id, user.id, "persistent_roles", None)
                await ctx.reply("Persistent roles cleared for user `{}`!".format(ctx.arg_str))
            else:
                # The user doesn't exist
                await ctx.reply("This user isn't known to Discord!")
    else:
        # Usage statement
        await ctx.reply("Please see `{}help forgetuser` for usage!".format((await ctx.bot.get_prefixes(ctx))[0]))


async def recall_roles(bot, member):
    # Quit if server doesn't have persistence enabled
    persist = await bot.data.servers.get(member.server.id, "role_persistence")
    if persist is not None and not persist:
        return

    # Quit if member has no stored roles
    stored = await bot.data.members_long.get(member.server.id, member.id, "persistent_roles")
    if stored is None or not stored:
        return

    # Build a list of roles which we have permission to add
    manager_roles = [r.position for r in member.server.me.roles if r.permissions.manage_roles or r.permissions.administrator]
    my_top_managerrole = max(manager_roles)
    roles_to_add = []

    for role in stored:
        actual_role = discord.utils.get(member.server.roles, id=role)
        if actual_role and actual_role.position < my_top_managerrole:
            roles_to_add.append(actual_role)

    # Give the member their roles, in theory
    try:
        await bot.add_roles(member, *roles_to_add)
    except discord.Forbidden:
        pass


async def store_roles(bot, member):
    role_list = [role.id for role in member.roles]
    await bot.data.members_long.set(member.server.id, member.id, "persistent_roles", role_list)


def load_into(bot):
    bot.data.servers.ensure_exists("role_persistence")
    bot.data.members_long.ensure_exists("persistent_roles")

    bot.add_after_event("member_join", recall_roles)
    bot.add_after_event("member_remove", store_roles)
