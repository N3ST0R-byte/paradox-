from typing import Any, List

from cmdClient import cmdClient

from registry import tableInterface  # noqa, imported for typing


class ListData:
    """
    Mixin for list types implemented on a tableInterface.
    Implements a reader and writer.
    """
    # Name of table interface to use for storage access
    _table_interface_name = None

    # Name of the column storing the guild id
    _guildid_column = "guildid"

    # Name of the column with the desired data
    _data_column = None

    @classmethod
    def _reader(cls, client: cmdClient, guildid: int, **kwargs):
        """
        Read in all entries associated to the guild.
        """
        table = cls._get_table_interface(client)  # type: tableInterface
        params = {
            "select_columns": [cls._data_column],
            cls._guildid_column: guildid
        }
        rows = table.select_where(**params)
        return [row[cls._data_column] for row in rows]

    @classmethod
    def _writer(cls, client: cmdClient, guildid: int, data: List[Any], **kwargs):
        """
        Write the provided list to storage.
        """
        # TODO: Accept kwargs for pure addition or removal of items
        # TODO: Compare existing values in table to avoid double-handling data
        # TODO: Transaction lock on the table so this is atomic

        table = cls._get_table_interface(client)  # type: tableInterface
        params = {
            cls._guildid_column: guildid
        }

        # Delete the setting for this guild
        table.delete_where(**params)

        # If there is data added, add the setting entries.
        if data:
            columns = (cls._guildid_column, cls._data_column)
            values = [(guildid, value) for value in data]
            table.insert_many(*values, insert_keys=columns)

    @classmethod
    def _get_table_interface(cls, client: cmdClient):
        """
        Gets the table interface from the client.
        """
        return client.data.interfaces.get(cls._table_interface_name)
