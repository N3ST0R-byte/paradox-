import logging
from paraModule import paraModule
from registry import propInterface, tableInterface, schema_generator, Column, ColumnType

"""
Define core shared data for paradoxical instances.
Specifically:
    Define the key-value property tables (deprecated, soon to be removed)
    Define the version table and check the current version matches.
"""

REQUIRED_DATA_VERSION = 1


# ------------------------------
# Version table and checker
# ------------------------------
version_mysql, version_sqlite, version_columns = schema_generator(
    "VERSION",
    Column("version", ColumnType.INT, required=True, primary=True),
    Column("updated_at", ColumnType.TIMESTAMP, default="CURRENT_TIMESTAMP", required=True),
    Column("updated_by", ColumnType.SHORTSTRING)
)
version_mysql += (
    "\n"
    "INSERT INTO VERSION (version, updated_by) VALUES ({}, 'Initial Creation');"
).format(REQUIRED_DATA_VERSION)
version_sqlite += (
    "\n"
    "INSERT INTO VERSION (version, updated_by) VALUES ({}, 'Initial Creation');"
).format(REQUIRED_DATA_VERSION)

versionModule = paraModule(
    "version_table",
    description="Skeleton module which loads the version table and checks the version on startup."
)


@versionModule.data_init_task
def load_version_table(client):
    interface = tableInterface(
        client.data,
        "VERSION",
        app=client.app,
        column_data=version_columns,
        shared=True,
        sqlite_schema=version_sqlite,
        mysql_schema=version_mysql,
    )
    client.data.attach_interface(interface, "version")


class DataVersionMismatch(Exception):
    """
    Custom exception class indicating the current data version is incorrect.
    """


@versionModule.init_task
def check_data_version(client):
    versions = client.data.version.select_where()
    if versions:
        version = max(row['version'] for row in versions)
        if version != REQUIRED_DATA_VERSION:
            client.log(
                "Refusing to start the client due to data version mismatch! "
                "Current data version is `{}`, required version is `{}`. "
                "Shutting down the client.".format(version, REQUIRED_DATA_VERSION),
                level=logging.CRITICAL,
                context="DATA_VERSION"
            )
            raise DataVersionMismatch(
                "Current version `{}` not equal to required version `{}`".format(version, REQUIRED_DATA_VERSION)
            )
        else:
            client.log("Current data version is `{}`.".format(version),
                       context="DATA_VERSION")
    else:
        client.log(
            "Refusing to start the client due to nonexistent version! "
            "Required version is `{}`, but no version was found in the database. "
            "Shutting down the client.".format(REQUIRED_DATA_VERSION),
            level=logging.CRITICAL,
            context="DATA_VERSION"
        )
        raise DataVersionMismatch("No version in database. Required version is `{}`".format(REQUIRED_DATA_VERSION))


# ------------------------------
# Define property tables (deprecated)
# ------------------------------

# Property table information
prop_table_info = [
        ("users", "users", ["userid"]),
        ("guilds", "guilds", ["guildid"]),
        ("members", "members", ["guildid", "userid"])
]

propertyModule = paraModule(
    "property_tables",
    description="Skeleton module which loads the core property tables."
)


@propertyModule.data_init_task
def load_property_tables(client):
    # Get the current app name
    app = client.conf.get("APP", "")

    # If the app is default the db app is empty
    if app in ["default", "paradox"]:
        app = ""

    # Get the data connector
    conn = client.data

    for attr, table, keys in prop_table_info:
        interface = propInterface(conn, table, keys, app)
        conn.attach_interface(interface, attr)
