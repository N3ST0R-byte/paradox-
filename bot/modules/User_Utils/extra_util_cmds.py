import discord
from datetime import datetime
from pytz import timezone
import aiohttp
import string

from paraCH import paraCH

cmds = paraCH()


@cmds.cmd("echo",
          category="Utility",
          short_help="Sends what you tell me to!")
async def cmd_echo(ctx):
    """
    Usage:
        {prefix}echo <text>
    Description:
        Replies to the message with <text>.
    """
    await ctx.reply(ctx.arg_str if ctx.arg_str else "I can't send an empty message!")


@cmds.cmd("jumpto",
          category="Utility",
          short_help="Generates a jump to link with a given message ID.")
@cmds.require("in_server")
async def cmd_jumpto(ctx):
    """
    Usage:
        {prefix}jumpto <msgid>
    Description:
        Replies with the jumpto link for the given message.
    Examples:
        {prefix}jumpto {msg.id}
    """
    msgid = ctx.arg_str
    if msgid == "" or not msgid.isdigit():
        await ctx.reply("Please provide a valid message ID.")
        return
    message = None
    try:
        message = await ctx.bot.get_message(ctx.ch, msgid)
    except Exception:
        pass
    for channel in ctx.server.channels:
        if message:
            break
        if channel.type != discord.ChannelType.text:
            continue
        if channel == ctx.ch:
            continue
        try:
            message = await ctx.bot.get_message(channel, msgid)
        except Exception:
            pass
    if not message:
        await ctx.reply("Couldn't find the message!")
        return
    embed = discord.Embed(colour=discord.Colour.green(), description="[Jump to message {}]({})".format(msgid, ctx.msg_jumpto(message)))
    await ctx.reply(embed=embed)


@cmds.cmd("quote",
          category="Utility",
          short_help="Quotes a message by ID")
@cmds.execute("flags", flags=["a", "r"])
@cmds.require("in_server")
async def cmd_quote(ctx):
    """
    Usage:
        {prefix}quote <messageid> [-a]
    Description:
        Replies with the specified message in an embed.
        Note that the message must be from the same server.
    Flags:
        -a:  (anonymous) Removes author information from the quote.
        -r: (raw) Gives the raw message instead of an embed.
    """
    msgid = ctx.arg_str
    if msgid == "" or not msgid.isdigit():
        await ctx.reply("Please provide a valid message ID.")
        return
    out_msg = await ctx.reply("Searching for message, please wait {}".format(ctx.aemoji_mention(ctx.bot.objects["emoji_loading"])))

    message = None
    try:
        message = await ctx.bot.get_message(ctx.ch, msgid)
    except Exception:
        pass
    if not message:
        message = await ctx.find_message(msgid, ignore=[ctx.ch])
    if not message:
        await ctx.bot.edit_message(out_msg, "Couldn't find the message!")
        return

    quote_content = message.content.replace("```", "[CODEBLOCK]") if ctx.flags['r'] else message.content

    header = "[Click to jump to message]({})".format(ctx.msg_jumpto(message))
    blocks = ctx.split_text(quote_content, 1000, code=ctx.flags['r'])

    embeds = []
    for block in blocks:
        desc = header + "\n" + block
        embed = discord.Embed(colour=discord.Colour.light_grey(),
                              description=desc,
                              timestamp=datetime.now())

        if not ctx.flags["a"]:
            embed.set_author(name="{user.name}".format(user=message.author),
                             icon_url=message.author.avatar_url)
        embed.set_footer(text="Sent in #{}".format(message.channel.name))
        if message.attachments:
            embed.set_image(url=message.attachments[0]["proxy_url"])
        embeds.append(embed)

    if len(embeds) == 1:
        await ctx.bot.edit_message(out_msg, " ", embed=embed)
    else:
        await ctx.bot.delete_message(out_msg)
        await ctx.pager(embeds, embed=True, locked=False)


@cmds.cmd("secho",
          category="Utility",
          short_help="Like echo but deletes.")
async def cmd_secho(ctx):
    """
    Usage:
        {prefix}secho <text>
    Description:
        Replies to the message with <text> and deletes your message.
    """
    try:
        await ctx.bot.delete_message(ctx.msg)
    except Exception:
        pass
    await ctx.reply("{}".format(ctx.arg_str) if ctx.arg_str else "I can't send an empty message!")


@cmds.cmd("invitebot",
          category="Utility",
          short_help="Generates a bot invite link for a bot",
          aliases=["ibot"])
@cmds.execute("user_lookup", in_server=True, greedy=True)
async def cmd_invitebot(ctx):
    """
    Usage:
        {prefix}invitebot <bot>
    Description:
        Replies with an invite link for the bot.
    """
    user = ctx.objs["found_user"]
    if ctx.arg_str.isdigit():
        userid = ctx.arg_str
    elif not user:
        await ctx.reply("I couldn't find any matching bots in this server")
        return
    elif not user.bot:
        await ctx.reply("Maybe you could try asking them nicely?")
        return
    if user:
        userid = user.id
    await ctx.reply("<https://discordapp.com/api/oauth2/authorize?client_id={}&permissions=0&scope=bot>".format(userid))


@cmds.cmd("piggybank",
          category="Utility",
          short_help="Keep track of money added towards a goal.",
          aliases=["bank"])
async def cmd_piggybank(ctx):
    """
    Usage:
        {prefix}piggybank [+|- <amount>] | [list [clear]] | [goal <amount>|none]
    Description:
        [+|- <amount>]: Adds or removes an amount to your piggybank.
        [list [clear]]: Sends you a DM with your previous transactions or clears your history.
        [goal <amount>|none]: Sets your goal!
        Or with no arguments, lists your current amount and progress to the goal.
    """
    bank_amount = await ctx.data.users.get(ctx.authid, "piggybank_amount")
    transactions = await ctx.data.users_long.get(ctx.authid, "piggybank_history")
    goal = await ctx.data.users.get(ctx.authid, "piggybank_goal")
    bank_amount = bank_amount if bank_amount else 0
    transactions = transactions if transactions else {}
    goal = goal if goal else 0
    if ctx.arg_str == "":
        msg = "You have ${:.2f} in your piggybank!".format(bank_amount)
        if goal:
            msg += "\nYou have achieved {:.1%} of your goal (${:.2f})".format(bank_amount / goal, goal)
        await ctx.reply(msg)
        return
    elif (ctx.params[0] in ["+", "-"]) and len(ctx.params) == 2:
        action = ctx.params[0]
        now = datetime.utcnow().strftime('%s')
        try:
            amount = float(ctx.params[1].strip("$#"))
        except ValueError:
            await ctx.reply("The amount must be a number!")
            return
        transactions[now] = {}
        transactions[now]["amount"] = "{}${:.2f}".format(action, amount)
        bank_amount += amount if action == "+" else -amount
        await ctx.data.users.set(ctx.authid, "piggybank_amount", bank_amount)
        await ctx.data.users_long.set(ctx.authid, "piggybank_history", transactions)
        msg = "${:.2f} has been {} your piggybank. You now have ${:.2f}!".format(amount,
                                                                                 "added to" if action == "+" else "removed from",
                                                                                 bank_amount)
        if goal:
            if bank_amount >= goal:
                msg += "\nYou have achieved your goal!"
            else:
                msg += "\nYou have now achieved {:.1%} of your goal (${:.2f}).".format(bank_amount / goal, goal)
        await ctx.reply(msg)
    elif (ctx.params[0] == "goal") and len(ctx.params) == 2:
        if ctx.params[1].lower() in ["none", "remove", "clear"]:
            await ctx.data.users.set(ctx.authid, "piggybank_goal", amount)
            await ctx.reply("Your goal has been cleared")
            return
        try:
            amount = float(ctx.params[1].strip("$#"))
        except ValueError:
            await ctx.reply("The amount must be a number!")
            return
        await ctx.data.users.set(ctx.authid, "piggybank_goal", amount)
        await ctx.reply("Your goal has been set to ${}. ".format(amount))
    elif (ctx.params[0] == "list"):
        if len(transactions) == 0:
            await ctx.reply("No transactions to show! Start adding money to your piggy bank with `{}piggybank + <amount>`".format(ctx.used_prefix))
            return
        if (len(ctx.params) == 2) and (ctx.params[1] == "clear"):
            await ctx.data.users_long.set(ctx.authid, "piggybank_history", {})
            await ctx.reply("Your transaction history has been cleared!")
            return

        msg = "```\n"
        for trans in sorted(transactions):
            trans_time = datetime.utcfromtimestamp(int(trans))
            tz = await ctx.data.users.get(ctx.authid, "tz")
            if tz:
                try:
                    TZ = timezone(tz)
                except Exception:
                    pass
            else:
                TZ = timezone("UTC")
            timestr = '%I:%M %p, %d/%m/%Y (%Z)'
            timestr = TZ.localize(trans_time).strftime(timestr)
            msg += "{}\t {:^10}\n".format(timestr, str(transactions[trans]["amount"]))
        await ctx.reply(msg + "```", dm=True)
    else:
        await ctx.reply("Usage: {}piggybank [+|- <amount>] | [list] | [goal <amount>|none]".format(ctx.used_prefix))


@cmds.cmd(name="colour",
          category="Utility",
          short_help="Displays information about a colour",
          aliases=["color"])
async def cmd_colour(ctx):
    """
    Usage:
        {prefix}colour <hexvalue>
    Description:
        Displays some detailed information about the colour, including a picture.
    Examples:
        {prefix}colour #0047AB
        {prefix}colour 0047AB
    """
    # TODO: Support for names, rgb etc as well
    hexstr = ctx.arg_str.strip("#")
    if not (len(hexstr) == 6 and all(c in string.hexdigits for c in hexstr)):
        await ctx.reply("Please give me a valid hex colour (e.g. #0047AB)")
        return
    fetchstr = "http://thecolorapi.com/id?hex={}&format=json".format(hexstr)
    async with aiohttp.get(fetchstr) as r:
        if r.status == 200:
            js = await r.json()
            inverted = col_invert(hexstr)
            prop_list = ["rgb", "hsl", "hsv", "cmyk", "XYZ"]
            value_list = [js[prop]["value"][len(prop):] for prop in prop_list]
            desc = ctx.prop_tabulate(prop_list, value_list)
            embed = discord.Embed(title="Colour info for `#{}`".format(hexstr), color=discord.Colour(int(hexstr, 16)), description=desc)
            embed.set_thumbnail(url="http://placehold.it/150x150.png/{}/{}?text={}".format(hexstr, inverted, "%23" + hexstr))
            embed.add_field(name="Closest named colour", value="`{}` (Hex `{}`)".format(js["name"]["value"], js["name"]["closest_named_hex"]))
            await ctx.reply(embed=embed)
        else:
            await ctx.reply("Sorry, something went wrong while fetching your colour! Please try again later")
            return


def col_invert(color_to_convert):
    table = str.maketrans('0123456789abcdef', 'fedcba9876543210')
    return color_to_convert.lower().translate(table).upper()


@cmds.cmd(name="names",
          category="Info",
          short_help="Lists previous recorded names for a user.",
          aliases=["namesfor", "whowas"])
@cmds.execute("user_lookup", in_server=True, greedy=True)
async def cmd_names(ctx):
    """
    Usage:
        {prefix}names [user]
    Description:
        Displays the past names I have seen for the provided user, or yourself.
    """
    user = ctx.author
    if ctx.arg_str != "":
        user = ctx.objs["found_user"]
        if not user:
            await ctx.reply("No matching users found in this server!")
            return
    usernames = await ctx.bot.data.users_long.get(user.id, "name_history")
    if not usernames:
        await ctx.reply("I haven't seen this user change their name!")
        return
    await ctx.pager(ctx.paginate_list(usernames, title="Usernames for {}".format(user)))


def load_into(bot):
    bot.data.users.ensure_exists("piggybank_amount", "piggybank_goal", shared=False)
    bot.data.users_long.ensure_exists("piggybank_history", shared=False)
