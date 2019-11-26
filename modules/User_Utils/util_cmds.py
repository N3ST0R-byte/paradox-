from paraCH import paraCH
import discord
import aiohttp
from PIL import Image
from io import BytesIO


cmds = paraCH()
# Provides rotate


@cmds.cmd("rotate",
          category="Utility",
          short_help="Rotates the last sent image.")
async def cmd_rotate(ctx):
    """
    Usage:
        {prefix}rotate [amount]
    Description:
        Rotates the attached image or the last sent image (within the last 10 messages) by <amount>.
        If <amount> is not specified, rotates backwards by 90.
    """
    amount = -1 * int(ctx.arg_str) if ctx.arg_str and (ctx.arg_str.isdigit() or (len(ctx.arg_str) > 1 and ctx.arg_str[0] == '-' and ctx.arg_str[1:].isdigit())) else 90
    try:
        message_list = ctx.bot.logs_from(ctx.ch, limit=10)
    except discord.Forbidden:
        await ctx.reply("I need permisions to get message logs to use this command")
        return
    file_dict = None
    async for message in message_list:
        if message.attachments and "height" in message.attachments[0]:
            file_dict = message.attachments[0]
            break
    if not file_dict:
        await ctx.reply("Couldn't find an attached image in the last 10 messages")
        return
    image_url = file_dict["url"]

    async with aiohttp.get(image_url) as r:
        response = await r.read()

    with Image.open(BytesIO(response)) as im:
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
            out_msg = await ctx.bot.send_file(ctx.ch, fp=output, filename="{}.png".format(file_dict["id"]))
            if out_msg:
                await ctx.offer_delete(out_msg)
