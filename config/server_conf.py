from contextBot.Conf import Conf
# from paraSetting import paraSetting
import settingTypes

server_conf = Conf("s_conf")


@server_conf.Setting
class Server_Setting_Prefix(settingTypes.STR):
    name = "guild_prefix"
    vis_name = "prefix"
    desc = "Custom server prefix"
    category = "Guild settings"

    '''
    @classmethod
    async def dyn_default(cls, ctx):
        return ctx.bot.prefix
    '''

# Join and leave message settings


@server_conf.Setting
class Server_Setting_Join(settingTypes.BOOL):
    name = "join_msgs_enabled"
    vis_name = "join"
    desc = "Enables/Disables join messages"
    default = False
    category = "Join message"

    outputs = {True: "Enabled",
               False: "Disabled"}


@server_conf.Setting
class Server_Setting_Join_Msg(settingTypes.FMTSTR):
    name = "join_msgs_msg"
    vis_name = "join_msg"
    desc = "Join message"
    default = "Give a warm welcome to $mention$!"
    category = "Join message"


@server_conf.Setting
class Server_Setting_Join_Ch(settingTypes.CHANNEL):
    name = "join_ch"
    vis_name = "join_ch"
    desc = "Channel to post in when a user joins"
    default = None
    category = "Join message"


@server_conf.Setting
class Server_Setting_Leave(settingTypes.BOOL):
    name = "leave_msgs_enabled"
    vis_name = "leave"
    desc = "Enables/Disables leave messages"
    default = False
    category = "Leave message"

    outputs = {True: "Enabled",
               False: "Disabled"}


@server_conf.Setting
class Server_Setting_Leave_Msg(settingTypes.FMTSTR):
    name = "leave_msgs_msg"
    vis_name = "leave_msg"
    desc = "Leave message"
    default = "Goodbye $username$, we hope you had a nice stay!"
    category = "Leave message"


@server_conf.Setting
class Server_Setting_Leave_Ch(settingTypes.CHANNEL):
    name = "leave_ch"
    vis_name = "leave_ch"
    desc = "Channel to post in when a user leaves"
    default = None
    category = "Leave message"


def load_into(bot):
    bot.add_to_ctx(server_conf)
    bot.s_conf = server_conf
