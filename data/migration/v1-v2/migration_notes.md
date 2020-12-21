# Migration from v1 to v2
Continuing the migration from the `key-value` property tables to individual data tables.

This version migrates the following features:
* Guild logging

# Migration operation
Apply the `mysql-schema.sql` or `sqlite-schema.sql` script to the database, as required.
The `sqlite` migration script does not migrate the old data, only updating the version and creating the new tables.


# Description of each of the properties in the v0 property tables, and subsequent action
Unless explicitly stated, value data is encoded by `json.dumps()` and may be reloaded into the actual values described below by `json.loads()`.

## `servers` table
