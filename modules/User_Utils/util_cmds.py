from paraCH import paraCH
import asyncio
import discord
import aiohttp
from PIL import Image
from io import BytesIO


cmds = paraCH()
# Provides rotate


@cmds.cmd("rotate",
          category="Utility",
          short_help="Rotates the last sent image.",
          aliases=['rcw', 'rccw'])
async def cmd_rotate(ctx):
    """
    Usage:
        {prefix}rotate [amount]
        {prefix}rcw [amount]
        {prefix}rccw [amount]
    Description:
        Rotates the attached image or the last sent image (within the last 10 messages) by <amount>.
        rcw rotates clockwise, rccw rotates counterclockwise, and rotate is by default clockwise.
        If <amount> is not specified, rotates by 90.
        (Note: If <amount> is not specified when used as "rotate", rotates by 90 degrees counterclockwise)
    """
    amount = -1 * int(ctx.arg_str) if ctx.arg_str and (ctx.arg_str.isdigit() or (len(ctx.arg_str) > 1 and ctx.arg_str[0] == '-' and ctx.arg_str[1:].isdigit())) else None
    amount = -1 * amount if amount is not None and ctx.used_cmd_name == "rccw" else amount
    amount = amount if amount is not None else (90 if ctx.used_cmd_name != "rcw" else -90)

    try:
        message_list = ctx.bot.logs_from(ctx.ch, limit=10)
    except discord.Forbidden:
        await ctx.reply("I need permisions to get message logs to use this command")
        return
    image_url = None
    async for message in message_list:
        if message.attachments and "height" in message.attachments[0]:
            image_url = message.attachments[0].get('url', None)
            break
        if message.embeds and message.embeds[0].get('type', None) == 'image':
            image_url = message.embeds[0].get('url', None)
            break

    if image_url is None:
        await ctx.reply("Couldn't find an attached image in the last 10 messages")
        return

    async with aiohttp.get(image_url) as r:
        response = await r.read()

    with Image.open(BytesIO(response)) as im:
        await _rotate(ctx, im, amount, ctx.author.id)

emoji_rotate_cw = "↩️"
emoji_rotate_ccw = "↪️"


async def _rotate(ctx, im, amount, name):
    exif = im.info.get('exif', None)
    rotated = im.rotate(amount, expand=1)
    bbox = rotated.getbbox()
    rotated = rotated.crop(bbox)
    with BytesIO() as output:
        if exif:
            rotated.convert("RGB").save(output, exif=exif, format="JPEG", quality=85, optimize=True)
        else:
            rotated.convert("RGB").save(output, format="JPEG", quality=85, optimize=True)
        output.seek(0)
        out_msg = await ctx.bot.send_file(ctx.ch, fp=output, filename="{}.png".format(name))
        if out_msg:
            try:
                await ctx.bot.add_reaction(out_msg, emoji_rotate_ccw)
                await ctx.bot.add_reaction(out_msg, emoji_rotate_cw)
                asyncio.ensure_future(ctx.offer_delete(out_msg))
            except discord.Forbidden:
                return
            while True:
                res = await ctx.bot.wait_for_reaction(
                    message=out_msg,
                    timeout=300,
                    user=ctx.author,
                    emoji=[emoji_rotate_cw, emoji_rotate_ccw]
                )
                if res is None:
                    try:
                        await ctx.bot.remove_reaction(out_msg, emoji_rotate_cw, ctx.me)
                        await ctx.bot.remove_reaction(out_msg, emoji_rotate_ccw, ctx.me)
                    except Exception:
                        pass
                    return
                await ctx.bot.delete_message(out_msg)
                await _rotate(ctx, im, amount + (90 if res.reaction.emoji == emoji_rotate_ccw else -90), name)
