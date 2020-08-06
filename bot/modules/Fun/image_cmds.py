import discord
import requests
import urllib
import random

from cmdClient import Context
from utils.ctx_addons import offer_delete

from .module import fun_module as module

# Provides cat, duck, dog, image
"""
Provides some image oriented fun commands

Commands provided:
    cat:
        Sends cat images
    dog:
        Sends dog images
    duck:
        Sends duck images
    holo:
        Sends holo images (and quotes)
    image:
        Searches for an image on Pixabay
"""


@module.cmd("image",
            desc="Searches Pixabay for images matching the specified text.",
            aliases=["imagesearch", "images", "img"])
async def cmd_image(ctx: Context):
    """
    Usage``:
        {prefix}image <image text>
    Description:
        Replies with a random image matching the search description from Pixabay.
    """

    # Pixabay API Key
    # Yeah it shouldn't really be here, but it's a free key with no limitations
    API_KEY = "10259038-12ef42751915ae10017141c86"

    if not ctx.arg_str:
        await ctx.reply("Please enter something to search for.")
        return
    search_for = urllib.parse.quote_plus(ctx.arg_str)
    r = requests.get('https://pixabay.com/api/?key={}&q={}&image_type=photo'.format(API_KEY, search_for))
    if r.status_code == 200:
        js = r.json()
        hits = js['hits'] if 'hits' in js else None
        if not hits:
            await ctx.reply("Didn't get any results for this query!")
            return
        hit_pages = []
        for hit in [random.choice(hits) for i in range(20)]:
            embed = discord.Embed(title="Here you go!", color=discord.Colour.light_grey())
            if "webformatURL" in hit:
                embed.set_image(url=hit["webformatURL"])
            else:
                continue
            embed.set_footer(text="Images thanks to the free Pixabay API!")
            hit_pages.append(embed)
        await ctx.offer_delete(await ctx.pager(hit_pages, embed=True))
    else:
        return await ctx.error_reply("An error occurred while fetching images. Please try again later.")


@module.cmd("dog",
            desc="Sends a random dog image",
            aliases=["doge", "pupper", "doggo", "woof"])
async def cmd_dog(ctx: Context):
    """
    Usage``:
        {prefix}dog
    Description:
        Replies with a random dog image!
    """
    BASE_URL = "http://random.dog/"
    r = requests.get("http://random.dog/woof")
    if r.status_code == 200:
        dog = r.text
        embed = discord.Embed(description="[Woof!]({})".format(BASE_URL + dog), color=discord.Colour.light_grey())
        try:
            embed.set_image(url=BASE_URL + dog)
        except Exception:
            return await ctx.error_reply("The file returned was an invalid format. Please try again.")
        else:
            await ctx.reply(embed=embed)
    else:
        return await ctx.error_reply("An error occurred while fetching dogs. Please try again later.")


@module.cmd("duck",
            desc="Sends a random duck image",
            aliases=["quack"],
            flags=["g"])
async def cmd_duck(ctx: Context, flags):
    """
    Usage``:
        {prefix}duck
    Description:
        Replies with a random duck image!
    """
    img_type = "gif" if flags["g"] else random.choice(["gif", "jpg"])
    r = requests.get('http://random-d.uk/api/v1/quack?type={}'.format(img_type))
    if r.status_code == 200:
        js = r.json()
        embed = discord.Embed(description="[Quack!]({})".format(js['url']), color=discord.Colour.light_grey())
        embed.set_image(url=js['url'])
        await ctx.reply(embed=embed)
    else:
        return await ctx.error_reply("An error occurred while fetching ducks. Please try again later.")


@module.cmd("cat",
            short_help="Sends a random cat image",
            aliases=["meow", "purr", "pussy"])
async def cmd_cat(ctx: Context):
    """
    Usage``:
        {prefix}cat
    Description:
        Replies with a random cat image!
    """
    r = requests.get('https://api.thecatapi.com/v1/images/search')
    if r.status_code == 200:
        js = r.json()
        embed = discord.Embed(description="[Meow!]({})".format(js[0]["url"]), color=discord.Colour.light_grey())
        embed.set_image(url=js[0]["url"])
        await ctx.reply(embed=embed)

    else:
        return await ctx.error_reply("An error occurred while fetching cats. Please try again later.")


@module.cmd("holo",
            short_help="Holo")
async def cmd_holo(ctx):
    """
    Usage``:
        {prefix}holo
    Image:
        Sends a picture of holo, and a random quote
    """
    r = requests.get('http://images.thewisewolf.dev/random')
    if r.status_code == 200:
        js = r.json()
        quote = "\"{}\"".format(js["quote"])
        embed = discord.Embed(description=quote, color=discord.Colour.light_grey())
        embed.set_image(url=js['image'])
        await ctx.reply(embed=embed)

    else:
        return await ctx.error_reply("Holo isn't available right now, please come back later")
