import sys
import platform
import psutil
import inspect
# from datetime import datetime

import discord
from cmdClient import Context

from utils.lib import prop_tabulate
from utils.ctx_addons import best_prefix  # noqa

from .module import meta_module as module


"""
Commands providing basic meta information about the bot.

Commands provided:
    about:
        Sends an embed with the status of the bot process,
        and statistics about the current shard client.
    ping:
        Test the API round trip response time through message edits.
    invite:
        Reply with an invite link for the current app.
    support:
        Reply with an invite link to the support guild for the current app.
    showcmd:
        Shows the source of a specified command (hidden).
"""


@module.cmd("about",
            desc="Shard status and bot statistics.")
async def cmd_about(ctx: Context):
    """
    Usage``:
        {prefix}about
    Description:
        Sends an embed with basic statistics about the current shard, host, and bot process.
    """
    table_fields = []

    # Current developers
    current_devs = ctx.client.app_info["dev_list"]
    dev_str = ", ".join(str(ctx.client.get_user(devid) or devid) for devid in current_devs)
    table_fields.append(("Developers", dev_str))

    # Shards, guilds, and members
    if ctx.client.shard_count > 1:
        shard_str = "{} of {}".format(ctx.client.shard_id, ctx.client.shard_count)
        table_fields.append(("Shard", shard_str))

        guild_str = "{} (~{} total)".format(
            len(ctx.client.guilds),
            ctx.client.shard_count * len(ctx.client.guilds)
        )
        table_fields.append(("Shard guilds", guild_str))

        member_str = "{} (~{} total)".format(
            len(list(ctx.client.get_all_members())),
            ctx.client.shard_count * len(list(ctx.client.get_all_members()))
        )
        table_fields.append(("Shard members", member_str))
    else:
        table_fields.append(("Guilds", len(ctx.client.guilds)))
        table_fields.append(("Members", len(list(ctx.client.get_all_members()))))

    # Commands
    table_fields.append((
        "Commands",
        "{}, with {} command keywords".format(len(ctx.client.cmds), len(ctx.client.cmd_names))
    ))

    # Memory
    mem = psutil.virtual_memory()
    mem_str = "{0:.2f}GB used out of {1:.2f}GB ({mem.percent}%)".format(
        mem.used/(1024 ** 3), mem.total/(1024 ** 3), mem=mem
    )
    table_fields.append(("Memory", mem_str))

    # CPU Usage
    table_fields.append((
        "CPU Usage",
        "{}%".format(psutil.cpu_percent())
    ))

    # API version
    table_fields.append((
        "API version",
        "{} ({})".format(discord.__version__, discord.version_info[3])
    ))

    # Python version
    table_fields.append(("Py version", sys.version.split("\n")[0]))

    # Platform
    table_fields.append(("Platform", platform.platform()))

    # Tabulate
    fields, values = zip(*table_fields)
    table = prop_tabulate(fields, values)

    # Create info string for top of description
    info = ctx.client.app_info["info_str"].format(prefix=ctx.best_prefix())

    # Create link string for bottom of description
    links = ("[Support Server]({}), [Invite Me]({}), [Help keep me running!]({})".format(
        ctx.client.app_info["support_guild"],
        ctx.client.app_info["invite_link"],
        ctx.client.app_info["donate_link"]
    ))

    # Build embed
    desc = "{}\n{}\n{}".format(info, table, links)
    embed = discord.Embed(title="About Me", color=discord.Colour.red(), description=desc)

    # Finally, send embed
    await ctx.reply(embed=embed)


@module.cmd("ping",
            desc="Check heartbeat and API latency.",
            aliases=["pong"])
async def cmd_ping(ctx: Context):
    """
    Usage``:
        {prefix}ping
    Description:
        Test the API round trip response by editing a message.
        Also sends the websocket protocol latency (hearbeat).
    """
    # Edit a message and see how long it takes
    msg = await ctx.reply("Beep")
    await msg.edit(content="Boop")
    latency = ((msg.edited_at - msg.created_at).microseconds) // 1000

    await msg.edit(content="Ping: `{}`ms.\nHeartbeat: `{:.0f}`ms.".format(latency, ctx.client.latency * 1000))


# @cmds.cmd("invite",
#           category="Meta",
#           short_help="Sends the bot's invite link",
#           aliases=["inv"])
# async def cmd_invite(ctx):
#     """
#     Usage:
#         {prefix}invite
#     Description:
#         Replies with a link to invite me to your server.
#     """
#     await ctx.reply("Visit <{}> to invite me!".format(ctx.bot.objects["invite_link"]))


# @cmds.cmd("support",
#           category="Meta",
#           short_help="Sends the link to the bot guild")
# async def cmd_support(ctx):
#     """
#     Usage:
#         {prefix}support
#     Description:
#         Sends the invite link to my support guild.
#     """
#     await ctx.reply("Join my server at <{}>".format(ctx.bot.objects["support_guild"]))


# @module.cmd("showcmd",
#           category="Bot admin",
#           short_help="Shows the source of a command.",
#           edit_handler=cmds.edit_handler_rerun)
# async def cmd_showcmd(ctx):
#     """
#         Usage:
#             {prefix}showcmd cmdname
#         Description:
#             Replies with the source for the command <cmdname>
#     """
#     # Get the list of current active commands, including aliases
#     cmds = await ctx.get_cmds()

#     if not ctx.arg_str:
#         await ctx.reply("You must give me with a command name!")
#     elif ctx.arg_str not in cmds:
#         await ctx.reply("I don't recognise this command.")
#     else:
#         cmd_func = cmds[ctx.arg_str].func
#         source = inspect.getsource(cmd_func)
#         source = source.replace('```', '[codeblock]')
#         blocks = ctx.split_text(source, 1800, syntax='python')

#         await ctx.offer_delete(await ctx.pager(blocks, locked=False))
