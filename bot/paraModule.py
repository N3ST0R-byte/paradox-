import asyncio
from cmdClient import cmdClient, Module
from cmdClient.lib import SafeCancellation


class paraModule(Module):
    name = "Base module"

    def __init__(self, *args, description=None, hidden=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = description or "Paradox module"
        self.hidden = hidden

    async def pre_cmd(self, ctx):
        if ctx.guild:
            banned_cmds = await ctx.data.guilds.get(ctx.guild.id, "banned_cmds")
            if banned_cmds and ctx.cmd.name in banned_cmds:
                raise SafeCancellation()


cmdClient.baseModule = paraModule
