import os
import discord
import aiohttp

from datetime import datetime
from io import StringIO

from paraCH import paraCH

cmds = paraCH()

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, "preamble.tex"), 'r') as preamble:
    default_preamble = preamble.read()


async def show_config(ctx):
    # Grab the config values
    grab = ["latex_keep_msg", "latex_colour", "latex_alwaysmath", "latex_allowother", "latex_showname"]
    grab_names = ["keepmsg", "colour", "alwaysmath", "allowother", "showname"]

    values = []
    for to_grab in grab:
        values.append(await ctx.data.users.get(ctx.authid, to_grab))

    value_lines = []
    value_lines.append("Keeping your message after compilation" if values[0] or values[0] is None else "Deleting your message after compilation")
    value_lines.append("Using colourscheme `{}`".format(values[1] if values[1] is not None else "default"))
    value_lines.append(("`{}tex` renders in mathmode" if values[2] else "`{}tex` renders in textmode").format(ctx.used_prefix))
    value_lines.append("Other uses may view your source and errors" if values[3] else "Other users may not view your source and errors")
    value_lines.append("Your name shows on the compiled output" if values[4] or values[4] is None else "Your name is hidden on the compiled output")

    desc = "**Config Option Values:**\n{}".format(ctx.prop_tabulate(grab_names, value_lines))

    # Initialise the embed
    embed = discord.Embed(title="Personal LaTeX Configuration", color=discord.Colour.light_grey(), description=desc)

    preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
    header = ""
    if not preamble:
        header = "No custom user preamble set, using default preamble."
        preamble = default_preamble
        if ctx.server:
            server_preamble = await ctx.data.servers.get(ctx.server.id, "server_latex_preamble")
            if server_preamble:
                header = "No custom user preamble set, using server preamble."
                preamble = server_preamble

    preamble_message = "{}```tex\n{}\n```".format(header, preamble)

    if len(preamble) > 1000:
        temp_file = StringIO()
        temp_file.write(preamble)

        preamble_message = "{}\nSent via direct message".format(header)

        temp_file.seek(0)
        try:
            await ctx.bot.send_file(ctx.author, fp=temp_file, filename="current_preamble.tex", content="Current active preamble")
        except discord.Forbidden:
            preamble_message = "Attempted to send your preamble file by direct message, but couldn't reach you."

    embed.add_field(name="Current preamble", value=preamble_message)

    new_preamble = await ctx.data.users.get(ctx.authid, "limbo_preamble")
    new_preamble_message = "```tex\n{}\n```".format(new_preamble)
    if new_preamble and len(new_preamble) > 1000:
        temp_file = StringIO()
        temp_file.write(new_preamble)

        new_preamble_message = "Sent via direct message"

        temp_file.seek(0)
        try:
            await ctx.bot.send_file(ctx.author, fp=temp_file, filename="new_preamble.tex", content="Preamble awaiting approval.")
        except discord.Forbidden:
            new_preamble_message = "Attempted to send your preamble file by direct message, but couldn't reach you."

    if new_preamble:
        embed.add_field(name="Awaiting approval", value=new_preamble_message, inline=False)

    await ctx.reply(embed=embed)


@cmds.cmd("serverpreamble",
          category="Maths",
          short_help="Change the server LaTeX preamble",
          flags=["reset", "replace", "remove"])
@cmds.require("in_server")
@cmds.require("in_server_has_mod")
async def cmd_serverpreamble(ctx):
    """
    Usage:
        {prefix}serverpreamble [code] [--reset] [--replace] [--remove]
    Description:
        Modifies or displays the current server preamble.
        The server preamble is used for compilation when a user in the server has no personal preamble.
        If [code] is provided, adds this to the server preamble, or replaces it with --replace
    Flags:2
        reset::  Resets your preamble to the default.
        replace:: replaces your preamble with this code
        remove:: Removes all lines from your preamble containing the given text.
    """
    if ctx.flags["reset"]:
        await ctx.data.servers.set(ctx.server.id, "server_latex_preamble", None)
        await ctx.reply("The server preamble has been reset to the default!")
        return

    current_preamble = await ctx.data.servers.get(ctx.server.id, "server_latex_preamble")
    current_preamble = current_preamble if current_preamble else default_preamble

    if not ctx.arg_str and not ctx.msg.attachments:
        if len(current_preamble) > 1000:
            temp_file = StringIO()
            temp_file.write(current_preamble)

            temp_file.seek(0)
            await ctx.reply(file_data=temp_file, file_name="server_preamble.tex", message="Current server preamble")
        else:
            await ctx.reply("Current server preamble:\n```tex\n{}```".format(current_preamble))
        return

    ctx.objs["latex_handled"] = True

    file_name = "preamble.tex"
    if ctx.msg.attachments:
        file_info = ctx.msg.attachments[0]
        async with aiohttp.get(file_info['url']) as r:
            new_preamble = await r.text()
        file_name = file_info['filename']
    else:
        new_preamble = ctx.arg_str

    if not ctx.flags["replace"]:
        new_preamble = "{}\n{}".format(current_preamble, new_preamble)

    if ctx.flags["remove"]:
        if ctx.arg_str not in current_preamble:
            await ctx.reply("Couldn't find this string in any line of the server preamble!")
            return
        new_preamble = "\n".join([line for line in current_preamble.split("\n") if ctx.arg_str not in line])

    await ctx.data.servers.set(ctx.server.id, "server_latex_preamble", new_preamble)

    in_file = (len(new_preamble) > 1000)
    if in_file:
        temp_file = StringIO()
        temp_file.write(new_preamble)

    preamble_message = "See file below!" if in_file else "```tex\n{}\n```".format(new_preamble)

    embed = discord.Embed(title="New Server Preamble", color=discord.Colour.blue()) \
        .set_author(name="{} ({})".format(ctx.author, ctx.authid),
                    icon_url=ctx.author.avatar_url) \
        .add_field(name="Preamble", value=preamble_message, inline=False) \
        .add_field(name="Server", value="{} ({})".format(ctx.server.name, ctx.server.id), inline=False) \
        .set_footer(text=datetime.utcnow().strftime("Sent from {} at %-I:%M %p, %d/%m/%Y".format(ctx.server.name if ctx.server else "private message")))

    await ctx.bot.send_message(ctx.bot.objects["preamble_channel"], embed=embed)
    if in_file:
        temp_file.seek(0)
        await ctx.bot.send_file(ctx.bot.objects["preamble_channel"], fp=temp_file, filename=file_name)
    await ctx.reply("Your server preamble has been updated!")


@cmds.cmd("preamble",
          category="Maths",
          short_help="Change how your LaTeX compiles",
          aliases=["texconfig"])
@cmds.execute("flags", flags=["reset", "replace", "add", "approve==", "remove", "retract", "deny=="])
async def cmd_preamble(ctx):
    """
    Usage:
        {prefix}preamble [code] [--reset] [--replace] [--remove]
    Description:
        Displays the preamble currently used for compiling your latex code.
        If [code] is provided, adds this to your preamble, or replaces it with --replace
        Note that preambles must currently be approved by a bot manager, to prevent abuse.
    Flags:2
        reset::  Resets your preamble to the default.
        replace:: replaces your preamble with this code
        remove:: Removes all lines from your preamble containing the given text.
        retract:: Retract a pending preamble.
    """
    user_id = ctx.flags["approve"] or ctx.flags["deny"]
    if user_id:
        (code, msg) = await cmds.checks["manager_perm"](ctx)
        if code != 0:
            return
        if ctx.flags["approve"]:
            new_preamble = await ctx.data.users.get(user_id, "limbo_preamble")
            if not new_preamble:
                await ctx.reply("Nothing to approve. Perhaps this preamble was already approved?")
                return
            new_preamble = new_preamble if new_preamble.strip() else default_preamble
            await ctx.data.users.set(user_id, "latex_preamble", new_preamble)
            await ctx.reply("The preamble change has been approved")
        await ctx.data.users.set(user_id, "limbo_preamble", "")
        if ctx.flags["deny"]:
            await ctx.reply("The preamble change has been denied")
        return

    if ctx.flags["reset"]:
        await ctx.data.users.set(ctx.authid, "latex_preamble", None)
        await ctx.data.users.set(ctx.authid, "limbo_preamble", "")
        await ctx.reply("Your LaTeX preamble has been reset to the default!")
        return

    if ctx.flags["retract"]:
        await ctx.data.users.set(ctx.authid, "limbo_preamble", "")
        await ctx.reply("You have retracted your preamble request.")
        return

    if not ctx.arg_str and not ctx.msg.attachments:
        await show_config(ctx)
        return

    ctx.objs["latex_handled"] = True

    file_name = "preamble.tex"
    if ctx.msg.attachments:
        file_info = ctx.msg.attachments[0]
        async with aiohttp.get(file_info['url']) as r:
            new_preamble = await r.text()
        file_name = file_info['filename']
    else:
        new_preamble = ctx.arg_str

    current_preamble = await ctx.data.users.get(ctx.authid, "limbo_preamble")
    if not current_preamble:
        current_preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
        if not current_preamble and ctx.server:
            current_preamble = await ctx.data.servers.get(ctx.server.id, "server_latex_preamble")
        if not current_preamble:
            current_preamble = default_preamble

    if not ctx.flags["replace"]:
        new_preamble = "{}\n{}".format(current_preamble, new_preamble)

    if ctx.flags["remove"]:
        # TODO: Fix, Ugly
        if ctx.arg_str not in current_preamble:
            await ctx.reply("Couldn't find this in any line of your preamble!")
            return
        new_preamble = "\n".join([line for line in current_preamble.split("\n") if ctx.arg_str not in line])

    await ctx.data.users.set(ctx.authid, "limbo_preamble", new_preamble)

    in_file = (len(new_preamble) > 1000)
    if in_file:
        temp_file = StringIO()
        temp_file.write(new_preamble)

    preamble_message = "See file below!" if in_file else "```tex\n{}\n```".format(new_preamble)

    embed = discord.Embed(title="LaTeX Preamble Request", color=discord.Colour.blue()) \
        .set_author(name="{} ({})".format(ctx.author, ctx.authid),
                    icon_url=ctx.author.avatar_url) \
        .add_field(name="Requested preamble", value=preamble_message, inline=False) \
        .add_field(name="To Approve", value="`preamble --approve {}`".format(ctx.authid), inline=False) \
        .set_footer(text=datetime.utcnow().strftime("Sent from {} at %-I:%M %p, %d/%m/%Y".format(ctx.server.name if ctx.server else "private message")))
    await ctx.bot.send_message(ctx.bot.objects["preamble_channel"], embed=embed)
    if in_file:
        temp_file.seek(0)
        await ctx.bot.send_file(ctx.bot.objects["preamble_channel"], fp=temp_file, filename=file_name)
    await ctx.reply("Your new preamble has been sent to the bot managers for review!")


async def get_preamble(ctx):
    preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
    if not preamble and ctx.server:
        preamble = await ctx.data.servers.get(ctx.server.id, "server_latex_preamble")
    if not preamble:
        preamble = default_preamble
    return preamble


def load_into(bot):
    bot.add_to_ctx(get_preamble)
