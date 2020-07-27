import logging
from logging.handlers import RotatingFileHandler
import argparse

import discord
from cmdClient import cmdClient

from config import Conf
from logger import log, log_fmt
from apps import load_app

# Always load command modules last
import modules  # noqa


# ------------------------------
# Parse commandline arguments
# ------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--conf',
                    dest='config',
                    default='config/paradox.conf',
                    help="Path to configuration file.")
parser.add_argument('--shard',
                    dest='shard',
                    default=None,
                    type=int,
                    help="Shard number to run, if applicable.")

args = parser.parse_args()
config_file = args.config
shard_num = args.shard or 0

# ------------------------------
# Load the configuration file
# ------------------------------
section_name = "SHARD {}".format(shard_num) if shard_num is not None else "DEFAULT"
conf = Conf(config_file, section_name)

# ------------------------------
# Read the environment variables
# ------------------------------
PREFIX = conf.get("PREFIX")

# Discord channel ids for logging endpoints and internal communication
CHEAT_CH = conf.getint("CHEAT_CH")
FEEDBACK_CH = conf.getint("FEEDBACK_CH")
PREAMBLE_CH = conf.getint("PREAMBLE_CH")
GUILD_LOG_CH = conf.getint("GUILD_LOG_CH")
LOG_CHANNEL = conf.getint("LOG_CHANNEL")
ERROR_CHANNEL = conf.getint("ERROR_CHANNEL") or LOG_CHANNEL

# Shard info
SHARD_COUNT = conf.getint("SHARD_COUNT") or 1


# ------------------------------
# Initialise data
# ------------------------------
CURRENT_APP = conf.get("APP", "")

# Conditional import and setting of opts depending on the type of db
DB_TYPE = conf.get("DB_TYPE")
if not DB_TYPE or DB_TYPE.lower() == "sqlite":
    from registry.paradata_sqlite import BotData
    dbopts = {'data_file': conf.get("client_data_file")}
elif DB_TYPE == "mysql":
    from registry.paradata_mysql import BotData
    dbopts = {
        'username': conf.get('username'),
        'password': conf.get('password'),
        'host': conf.get('host'),
        'database': conf.get('database')
    }
else:
    raise Exception("Unknown data storage type {} in configuration".format(DB_TYPE))

clientdata = BotData(app=CURRENT_APP if CURRENT_APP is not "default" else "", **dbopts)


# ------------------------------
# Initialise the logger file handler
# ------------------------------
LOGFILE = conf.get("LOGFILE")

logger = logging.getLogger()
file_handler = RotatingFileHandler(
    filename=LOGFILE,
    maxBytes=5000000,
    backupCount=10,
    encoding='utf-8',
    mode='a'
)
file_handler.setFormatter(log_fmt)
logger.addHandler(file_handler)


# ------------------------------
# Set up the client
# ------------------------------

# Create the client
client = cmdClient(
    prefix=PREFIX,
    shard_id=shard_num,
    shard_count=SHARD_COUNT
)
client.data = clientdata
client.conf = conf

# Attach the relevant app information and hooks
load_app(CURRENT_APP or "default", client)


# Attach prefix function
client.objects["user_prefix_cache"] = {}
client.objects["guild_prefix_cache"] = {}


@client.set_valid_prefixes
async def get_prefixes(client, message):
    """
    Returns a list of valid prefixes for this message.
    """
    # Add both types of mentions, which are always valid prefixes
    prefixes = [client.user.mention, "<@!{}>".format(client.user.id)]

    # Add user prefix if it exists
    user_prefix = client.objects["user_prefix_cache"].get(message.author.id, None)
    if user_prefix is not None:
        prefixes.append(user_prefix)

    # Add guild prefix if it exists, otherwise add default prefix
    guild_prefix = None
    if message.guild:
        guild_prefix = client.objects["guild_prefix_cache"].get(message.guild.id, None)
    if guild_prefix is not None:
        prefixes.append(guild_prefix)
    else:
        prefixes.append(client.prefix)

    return prefixes


# --------------------------------
# Attach client event hooks
# ------------------------------

@client.event
async def on_ready():
    activity_name = "Type {}help for usage!".format(client.prefix)
    client.objects["activity_name"] = activity_name
    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name=activity_name)
    )

    await client.launch_modules()
    log_msg = ("Logged in as\n{client.user.name}\n{client.user.id}\n"
               "Using configuration {app}.\n"
               "Logged into {n} guilds on shard {shard}/{shard_count}.\n"
               "Loaded {m} modules with {mn} commands.\n"
               "Listening for {mnn} command keywords.\n"
               "Ready to take commands.".format(
                   client=client,
                   app=client.app_info['app'],
                   shard=shard_num,
                   shard_count=SHARD_COUNT,
                   n=len(client.guilds),
                   m=len(client.modules),
                   mn=len(client.cmds),
                   mnn=len(client.cmd_names)
               ))
    log(log_msg)

    client.objects["cheat_report_channel"] = discord.utils.get(client.get_all_channels(), id=CHEAT_CH)
    client.objects["feedback_channel"] = discord.utils.get(client.get_all_channels(), id=FEEDBACK_CH)
    client.objects["preamble_channel"] = discord.utils.get(client.get_all_channels(), id=PREAMBLE_CH)
    client.objects["guild_log_channel"] = discord.utils.get(client.get_all_channels(), id=GUILD_LOG_CH)


@client.event
async def on_message(message: discord.Message):
    # Handle messages from bot accounts
    if message.author.bot and message.author.id not in conf.getintlist("whitelisted_bots", []):
        return

    # Handle messages from blacklisted users
    if message.author.id in conf.getintlist("blacklisted_users", []):
        return
    await client.parse_message(message)

    if message.guild:
        # Handle messages from blacklisted guilds
        if message.author.id in conf.getintlist("blacklisted_guilds", []):
            return

        # Handle blacklisted guild channels
        # if (
        #     message.id in client.objects["guild_channel_blacklists"] and
        #     message.channel.id in client.objects["guild_channel_blacklists"][message.guild.id] and
        #     not message.author.server_permissions.administrator
        # ):
        #     return


# Initialise modules
client.initialise_modules()

# ----Everything is set up, start the client!----
client.run(conf.get("TOKEN"))
