class _guild_config:
    """
    Namespace class to hold the guild settings.
    """
    settings = {}
    __slots__ = tuple()

    def __init__(self):
        pass

    def attach_setting(self, cls):
        self.settings[cls.attr_name] = cls

    def __getattr__(self, attr):
        return self.settings.get(attr)


guild_config = _guild_config()
