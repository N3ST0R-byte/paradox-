import os
import configparser as cfgp

from paraEmoji import configEmoji


conf = None  # type: Conf


class Conf:
    def __init__(self, configfile, section_name="DEFAULT"):
        self.configfile = configfile
        self.section_name = section_name

        self.config = cfgp.ConfigParser(
            converters={
                "intlist": self._getintlist,
                "list": self._getlist,
                "emoji": configEmoji.from_str,
            }
        )
        self.config.read(configfile)

        self.section = self.config[section_name]
        self.default = self.config["DEFAULT"]

        global conf
        conf = self

    def __getitem__(self, key):
        return self.section[key].strip()

    def __getattr__(self, name):
        return getattr(self.section, name)

    def get(self, name, fallback=None):
        result = self.section.get(name, fallback)
        return result.strip() if result else result

    def _getintlist(self, value):
        return [int(item.strip()) for item in value.split(',')]

    def _getlist(self, value):
        return [item.strip() for item in value.split(',')]

    def write(self):
        with open(self.configfile, 'w') as conffile:
            self.config.write(conffile)


def get_conf():
    if conf is None:
        raise Exception("Retrieving configuration without initialisation.")
    return conf
