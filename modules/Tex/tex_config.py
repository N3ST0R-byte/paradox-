import os
import discord

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


async def get_preamble(ctx):
    preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
    if not preamble and ctx.server:
        preamble = await ctx.data.servers.get(ctx.server.id, "server_latex_preamble")
    if not preamble:
        preamble = default_preamble
    return preamble


def load_into(bot):
    bot.add_to_ctx(get_preamble)
