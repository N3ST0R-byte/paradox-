import os
from datetime import datetime
import discord

from paraCH import paraCH

cmds = paraCH()

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, "preamble.tex"), 'r') as preamble:
    default_preamble = preamble.read()

# The stored names of the LaTeX configuration values
grab = ["latex_keep_msg", "latex_colour", "latex_alwaysmath", "latex_allowother", "latex_showname"]

# The option names, used for display and setting
grab_names = ["keepmsg", "colour", "alwaysmath", "allowother", "showname"]


async def show_config(ctx, user=None):
    """
    Send an embed containing the current LaTeX configuration of user or ctx.author
    """
    user = user or ctx.author

    # Grab the config values
    values = []
    for to_grab in grab:
        values.append(await ctx.data.users.get(ctx.authid, to_grab))

    # List of lines to display, depending on the option values, corresponding to grab
    value_lines = [
        "Keeping your message after compilation" if values[0] or values[0] is None else "Deleting your message after compilation",
        "Using colourscheme `{}`".format(values[1] if values[1] is not None else "default"),
        "`{}tex` renders in mathmode" if values[2] else "`{}tex` renders in textmode".format(ctx.used_prefix),
        "Other uses may view your source and errors" if values[3] else "Other users may not view your source and errors",
        "Your name shows on the compiled output" if values[4] or values[4] is None else "Your name is hidden on the compiled output"
    ]

    # Description for the configuration embed
    desc = "**Settings:**\
    \n{values}\
    \n\nUse `{prefix}tex --option value` to set an option, e.g. `{prefix}tex --colour white`".format(
        values=ctx.prop_tabulate(grab_names, value_lines), prefix=ctx.used_prefix
    )

    # Initialise the embed
    embed = discord.Embed(title="Personal LaTeX Configuration",
                          color=discord.Colour.light_grey(),
                          description=desc,
                          timestamp=datetime.utcnow())
    field_lines = []  # List of lines to go into the preamble field

    # Identify what type of preamble the user is using, and construct the first line of the preamble field
    preamble = await ctx.data.users_long.get(ctx.authid, "latex_preamble")
    if preamble:
        header = "Using a custom preamble with {} lines!".format(len(preamble.splitlines()))
    else:
        header = "No custom user preamble set, using default preamble."
        if ctx.server:
            server_preamble = await ctx.data.servers_long.get(ctx.server.id, "server_latex_preamble")
            if server_preamble:
                header = "No custom user preamble set, using server preamble."
    field_lines.append(header)

    # Add the command hint for showing the preamble
    field_lines.append("Use `{}preamble` to see or modify the current preamble.".format(ctx.used_prefix))

    # Identify whether the user has a pending preamble, and if so add it as the last line
    pending = await ctx.bot.data.users_long.get(user.id, 'pending_preamble')
    if pending is not None:
        field_lines.append("New custom preamble submitted and awaiting approval.")

    # Add the preamble field
    embed.add_field(name="Custom preamble", value='\n'.join(field_lines))

    # Finally, send the config info to the user
    await ctx.reply(embed=embed)
