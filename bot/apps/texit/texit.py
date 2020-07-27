import os


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
HELP_FILE = os.path.join(__location__, "help.txt")

with open(HELP_FILE, "r") as help_file:
    help_str = help_file.read()


info = {
    "dev_list": [299175087389802496, 408905098312548362],
    "info_str": ("I am a high quality LaTeX rendering bot coded in discord.py.\n"
                 "Use `{prefix}help` for information on how to use me, "
                 "and `{prefix}list` to see all my commands!"),
    "invite_link": "http://texit.paradoxical.pw",
    "donate_link": "https://www.patreon.com/texit",
    "support_guild": "https://discord.gg/YNQzcvH",
    "brief": True,
    "app": "texit",
    "help_str": help_str,
    "help_file": "resources/apps/texit/texit_thanks.png"
}

disabled_modules = [
    "Fun",
    "Social",
    "extended_utils",
    "emoji",
]


async def enable_latex_listening(client, guild):
    listening = client.data.guilds.get(guild.id, "latex_listen_enabled")

    if listening is None:
        client.data.guilds.set(guild.id, "latex_listen_enabled", True)

        listens = client.objects["guild_tex_listeners"]
        channels = client.data.guilds.get(guild.id, "maths_channels")
        listens[str(guild.id)] = channels if channels else []


def load_into(client):
    client.data.guilds.ensure_exists("latex_listen_enabled", shared=False)
    client.add_after_event("guild_join", enable_latex_listening)
    client.app_info = info

    for module in client.modules:
        if module.name in disabled_modules:
            module.enabled = False
