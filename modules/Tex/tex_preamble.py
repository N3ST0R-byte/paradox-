import os
import asyncio
from datetime import datetime
from io import StringIO

import discord

from paraCH import paraCH

cmds = paraCH()

"""
Handle LaTeX preamble submission and approval/processing

Commands:
    preamble: User command to show or modify their preamble
    serverpreamble: Server command to show or modify server default preamble
    preambleadmin: Bot admin command to manage preamble submissions and individual preambles
"""


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, "preamble.tex"), 'r') as preamble:
    default_preamble = preamble.read()


def split_text(text, blocksize, code=True, syntax="", maxheight=50):
    # Break the text into blocks of maximum length blocksize
    # If possible, break across nearby newlines. Otherwise just break at blocksize chars
    blocks = []
    while True:
        if len(text) <= blocksize:
            blocks.append(text)
            break

        split_on = text[0:blocksize].rfind('\n')
        split_on = blocksize if split_on == -1 else split_on

        blocks.append(text[0:split_on])
        text = text[split_on:]

    # Add the codeblock ticks and the code syntax header, if required
    if code:
        blocks = ["```{}\n{}\n```".format(syntax, block) for block in blocks]

    return blocks


def tex_pagination(text, basetitle="", header=None, timestamp=True, colour=discord.Colour.dark_blue()):
    blocks = split_text(text, 1000, code=True, syntax="tex")

    blocknum = len(blocks)

    if blocknum == 1:
        return [discord.Embed(title=basetitle,
                              color=colour,
                              description=blocks[0],
                              timestamp=datetime.utcnow())]

    embeds = []
    for i, block in enumerate(blocks):
        desc = "{}\n{}".format(header, block) if header else block
        embed = discord.Embed(title=basetitle,
                              colour=colour,
                              description=desc,
                              timestamp=datetime.utcnow())
        embed.set_footer(text="Page {}/{}".format(i+1, blocknum))
        embeds.append(embed)

    return embeds


async def sendfile_reaction_handler(ctx, out_msg, temp_file, title):
    try:
        await ctx.bot.add_reaction(out_msg, ctx.bot.objects["emoji_sendfile"])
    except discord.Forbidden:
        return

    while True:
        res = await ctx.bot.wait_for_reaction(message=out_msg,
                                              emoji=ctx.bot.objects["emoji_sendfile"],
                                              timeout=300)
        if res is None:
            try:
                await ctx.bot.remove_reaction(out_msg, ctx.bot.objects["emoji_sendfile"], ctx.me)
            except Exception:
                pass
            break
        elif res.user != ctx.me:
            try:
                await ctx.bot.send_file(res.user, fp=temp_file, filename="preamble.tex", content=title)
            except discord.Forbidden:
                await ctx.reply("Sorry, I tried to DM the preamble file, but couldn't reach you!")
            except discord.HTTPException:
                pass
            try:
                await ctx.bot.remove_reaction(out_msg, ctx.bot.objects["emoji_sendfile"], res.user)
            except Exception:
                pass


async def view_preamble(ctx, preamble, title, header=None, file_react=False):
    pages = tex_pagination(preamble, basetitle=title, header=header)
    out_msg = await ctx.pager(pages, embed=True)

    if not file_react or out_msg is None:
        return

    # Generate file to send to user on reaction press
    with StringIO() as temp_file:
        temp_file.write(preamble)
        temp_file.seek(0)
        asyncio.ensure_future(sendfile_reaction_handler(ctx, out_msg, temp_file, title))

    return out_msg


async def confirm(ctx, question, preamble, **kwargs):
    out_msg = await view_preamble(ctx, preamble, "{} (y/n)".format(question), **kwargs)
    result_msg = await ctx.listen_for(["y", "yes", "n", "no"], timeout=120)

    if result_msg is None:
        return None
    result = result_msg.content.lower()
    try:
        await ctx.bot.delete_message(out_msg)
        await ctx.bot.delete_message(result_msg)
    except Exception:
        pass
    if result in ["n", "no"]:
        return False
    return True


@cmds.cmd("showpreamble",
          category="Maths",
          short_help="View or modify your LaTeX preamble")
async def cmd_showpreamble(ctx):
    """
    Usage:
        Magick
    """
    header = None
    preamble = await ctx.data.users.get(ctx.authid, "latex_preamble")
    if not preamble:
        preamble = default_preamble
        header = "No custom preamble set or server preamble found, using the default preamble!"

    await view_preamble(ctx, preamble, "Your current preamble", header=header, file_react=True)


def load_into(bot):
    pass
