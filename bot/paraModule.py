from cmdClient import cmdClient, Module
from cmdClient.lib import SafeCancellation

from settings import guild_config

from logger import log


class paraModule(Module):
    name = "Base module"

    def __init__(self, *args, description=None, hidden=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = description or "Paradox module"
        self.hidden = hidden

        self.data_init_tasks = []
        self.data_initialised = False

        self.guild_settings = []

    def guild_setting(self, cls):
        """
        Class decorator to attach a guild setting
        which will be later loaded on initialisation.
        """
        self.guild_settings.append(cls)
        log("Registering guild setting '{}'.".format(cls.attr_name), context=self.name)

    def initialise(self, client):
        if self.guild_settings and not self.initialised:
            log("Attaching guild settings.", context=self.name)
            for setting in self.guild_settings:
                log("Attaching guild setting '{}'.".format(setting.attr_name))
                guild_config.attach_setting(setting)
                setting.initialise(client)

        super().initialise(client)

    async def pre_cmd(self, ctx):
        if ctx.guild:
            banned_cmds = await ctx.data.guilds.get(ctx.guild.id, "banned_cmds")
            if banned_cmds and ctx.cmd.name in banned_cmds:
                raise SafeCancellation()

    def data_init_task(self, func):
        """
        Decorator which adds a data initialisation task.
        These tasks accept a client,
        but should not set up the client or assume any existing data or schema.
        The primary purpose is to attach the data interfaces for each module.
        """
        self.data_init_tasks.append(func)
        log("Adding data initialisation task '{}'.".format(func.__name__), context=self.name)
        return func

    def initialise_data(self, client):
        """
        Data initialise hook.
        """
        if not self.data_initialised:
            log("Running data initialisation tasks.", context=self.name)

            for task in self.data_init_tasks:
                log("Running data initialisation task '{}'.".format(task.__name__), context=self.name)
                task(client)

            self.data_initialised = True
        else:
            log("Already initialised data, skipping data initialisation.", context=self.name)


cmdClient.baseModule = paraModule
