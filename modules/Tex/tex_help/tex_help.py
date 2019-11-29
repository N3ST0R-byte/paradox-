import os
import asyncio

import discord

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

texblurblist = ['main.md']
texgiflist = ['main.gif', 'eqn.gif', 'align.gif']

texblurbs = {name: os.path.join(__location__, 'texblurbs', name) for name in texblurblist}
texgifs = {name: os.path.join(__location__, 'texgifs', name) for name in texgiflist}


async def formatblurb(ctx, blurbname):
    with open(os.path.join(__location__, texblurbs[blurbname]), 'r') as blurbfile:
        blurb = blurbfile.read()
    return blurb.format(
        prefix="",
        edelout=ctx.bot.objects["emoji_tex_del"],
        eshowsrc=ctx.bot.objects["emoji_tex_show"],
        edelsrc=ctx.bot.objects["emoji_tex_delsource"]
    )[:2000]


menu_entries = [
    ("🇦", "Fast Equations", "This is how you use the fast equation thingy", "eqn.gif"),
    ("🇧", "Fast `align` environment", "This is how you use the align thingy", "align.gif")
]


async def tex_extended_help(ctx, *args, help_embed=None, **kwargs):
    desc = "\n".join("{} {}".format(emoji, item) for emoji, item, _, _ in menu_entries)

    menu_embed = discord.Embed(title="Examples and features", colour=discord.Colour.blue(), description=desc)

    with open(texgifs['main.gif'], 'rb') as im:
        out_msg = await ctx.send(
            ctx.author,
            message=await formatblurb(ctx, 'main.md'),
            embed=menu_embed,
            file_data=im,
            file_name="LaTeX_Usage.gif"
        )
    asyncio.ensure_future(menu(ctx, out_msg))


async def menu(ctx, out_msg):

    emojis = [entry[0] for entry in menu_entries]

    for emoji in emojis:
        await ctx.bot.add_reaction(out_msg, emoji)

    prev_out = None
    while True:
        res = await ctx.bot.wait_for_reaction(message=out_msg, user=ctx.author, emoji=emojis, timeout=600)
        if res is None:
            return
        if prev_out is not None:
            await ctx.bot.delete_message(prev_out)

        i = emojis.index(res.reaction.emoji)
        entry_blurb, entry_image = menu_entries[i][2:]

        with open(texgifs[entry_image], 'rb') as im:
            prev_out = await ctx.send(
                ctx.author,
                message=entry_blurb,
                file_data=im,
                file_name="LaTeX_Usage.gif"
            )
