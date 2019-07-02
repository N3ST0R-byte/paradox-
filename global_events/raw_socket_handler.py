import os

cest_une_pipe = None


async def handle_raw_socket(bot, msg):
    global cest_une_pipe
    if (cest_une_pipe == None):
        app = os.getcwd().split(os.sep)[-1]
        cest_une_pipe = open("/home/paradox/pipe/"+app,"w")
    if isinstance(msg,str):
        cest_une_pipe.write(msg)
        cest_une_pipe.write('\n')


def load_into(bot):
    bot.add_after_event("socket_raw_receive", handle_raw_socket, priority=5)