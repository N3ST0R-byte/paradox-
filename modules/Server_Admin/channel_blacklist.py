"""
Channel blacklist registration.
"""


async def register_channel_blacklists(bot):
    channel_blacklists = {}
    for server in bot.servers:
        channels = await bot.data.servers.get(server.id, "channel_blacklist")
        if channels:
            channel_blacklists[server.id] = channels
    bot.objects["channel_blacklists"] = channel_blacklists
    await bot.log("Loaded {} servers with channel blacklists.".format(len(channel_blacklists)))


def load_into(bot):
    bot.data.servers.ensure_exists("channel_blacklist", shared=False)
    bot.add_after_event("ready", register_channel_blacklists)
