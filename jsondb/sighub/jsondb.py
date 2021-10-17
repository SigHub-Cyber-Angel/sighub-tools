""" A TinyDB wrapper (https://github.com/msiemens/tinydb) providing document based log
    database and configuration database functionality.
"""

from dataclasses import dataclass, InitVar, field
from datetime import datetime

from typing import (
    Dict,
    List
)

import enum
import json
import os
import sys

from tinydb import (
    TinyDB,
    Query
)

# LogDB log rotation measurement units


class RotateUnit(enum.Enum):
    """ Units in which RotatingLogDB should measure rotate_after.
    """
    BYTES = 'bytes'
    ENTRIES = 'entries'


@dataclass
class BaseDB:
    """ Base NoSQL database. All entries are stored in JSON object format (dict).

        Attributes:
            path: filesystem path for database storage
            table: set current table (can be changed using set_table)
            read_only: do not write to this database
    """
    path: str
    table: str
    read_only: bool

    def set_table(self, table):
        """ Set the table to perform operations on.
        """
        self.table = table

    def insert(self, entry):
        """ Insert an entry in the database.
        """
        if self.read_only:
            raise ReadOnlyError

        with TinyDB(self.path) as datastore:
            curr_table = datastore.table(self.table, cache_size=0)

            curr_table.insert(entry)

    def insert_multiple(self, entries):
        """ Insert multiple entries in the database.
        """
        if self.read_only:
            raise ReadOnlyError

        with TinyDB(self.path) as datastore:
            curr_table = datastore.table(self.table, cache_size=0)

            for entry in entries:
                curr_table.insert(entry)

    def update_insert(self, entry, filters):
        """ Update or insert an in the database based on the filters.
        """
        updated = []
        with TinyDB(self.path) as datastore:
            curr_table = datastore.table(self.table, cache_size=0)

            query = Query()

            updated = curr_table.upsert(entry, query.fragment(filters))

        return updated

    def get_all(self):
        """ Get all database entries.
        """
        _all = []
        with TinyDB(self.path) as datastore:
            curr_table = datastore.table(self.table, cache_size=0)

            _all = curr_table.all()

        return _all

    def get_matches(self, filters, negate=False):
        """ Get all entries that match the given key / value filters.
        """
        entries = []
        with TinyDB(self.path) as datastore:
            curr_table = datastore.table(self.table, cache_size=0)

            query = Query()

            if negate:
                entries = curr_table.search(~ query.fragment(filters))
            else:
                entries = curr_table.search(query.fragment(filters))

        return entries

    def delete_matches(self, filters):
        """ Delete all entries that match the given key / value filters.
        """
        deleted = []
        with TinyDB(self.path) as datastore:
            curr_table = datastore.table(self.table, cache_size=0)

            query = Query()

            deleted = curr_table.remove(query.fragment(filters))

        return deleted

    def get_field_in(self, key, values, negate=False):
        """ Get all entries if the key matches one of the given values.
        """
        entries = []
        with TinyDB(self.path) as datastore:
            curr_table = datastore.table(self.table, cache_size=0)

            query = Query()

            if negate:
                entries = curr_table.search(~ query[key].one_of(values))
            else:
                entries = curr_table.search(query[key].one_of(values))

        return entries


@dataclass
class LogDB(BaseDB):
    """ NoSQL database for log storage.

        Attributes:
            path: filesystem path for database storage
            table: logs table in the database
            read_only: do not write to this database
    """

    def append(self, entry):
        """ Append a log entry to the database.
            If the entry does not contain a 'ts' field one will be added.
            'ts' must be an integer or float.
        """
        if self.read_only:
            raise ReadOnlyError

        if 'ts' not in entry:
            entry['ts'] = datetime.timestamp(datetime.now())

        self.insert(entry)

    def append_multiple(self, entries):
        """ Append multiple log entries to the database.
            If the entrie do not contain a 'ts' field one will be added.
            'ts' must be an integer or float.
        """
        if self.read_only:
            raise ReadOnlyError

        for entry in entries:
            if 'ts' not in entry:
                entry['ts'] = datetime.timestamp(datetime.now())

        self.insert_multiple(entries)

    def get_after(self, unix_timestamp):
        """ Get all log entries after the given timestamp.
        """
        entries = []
        with TinyDB(self.path) as datastore:
            logs = datastore.table(self.table, cache_size=0)

            query = Query()

            entries = logs.search(query.ts > unix_timestamp)

        return entries

    def get_before(self, unix_timestamp):
        """ Get all log entries before the given timestamp.
        """
        entries = []
        with TinyDB(self.path) as datastore:
            logs = datastore.table(self.table, cache_size=0)

            query = Query()

            entries = logs.search(query.ts < unix_timestamp)

        return entries

    def get_between(self, start, end):
        """ Get all log entries between the starting and ending timestamps.
        """
        entries = []
        with TinyDB(self.path) as datastore:
            logs = datastore.table(self.table, cache_size=0)

            query = Query()

            entries = logs.search((query.ts >= start) & (query.ts <= end))

        return entries

    def delete_before(self, unix_timestamp):
        """ Delete all entries from the database from before the given timestamp.
            Returns True if entries were deleted.
        """
        deleted = []
        with TinyDB(self.path) as datastore:
            logs = datastore.table(self.table, cache_size=0)

            query = Query()

            deleted = logs.remove(query.ts < unix_timestamp)

        if not deleted:
            return False

        return True

@dataclass
class RotatingLogDB(LogDB):
    """ NoSQL database for rotating log storage.

        Attributes:
            path: filesystem path for database storage
            table: logs table in the database
            read_only: do not write to this database
            rotate_after: how many rotate_units trigger a rotation
            rotate_times: number of rotated log files to save
            rotate_path: base filename and path for rotated log files
            rotate_units: units to measure in in order to determine when to rotate log files
    """
    rotate_after: int
    rotate_times: int
    rotate_path: str
    rotate_units: RotateUnit = RotateUnit.ENTRIES

    def append(self, entry):
        """ Append a log entry to the database.
            If the entry does not contain a 'ts' field one will be added.
            'ts' must be an integer or float.
            If the log file is larger than rotate_after rotate_units, rotate_files will be called.
        """
        LogDB.append(self, entry)

        self.rotate_files()

    def append_multiple(self, entries):
        """ Append multiple log entries to the database.
            If the entrie do not contain a 'ts' field one will be added.
            'ts' must be an integer or float.
            If the log file is larger than rotate_after rotate_units, rotate_files will be called.
        """
        LogDB.append_multiple(self, entries)

        self.rotate_files()

    def rotate_files(self):
        """ Rotate the logs database file.
        """
        if self.read_only:
            raise ReadOnlyError

        rotation_path = None
        current_table = []
        with TinyDB(self.path) as datastore:
            logs = datastore.table(self.table, cache_size=0)

            # all log entries as a list
            current_table = list(logs.all())

            entries_greater = len(current_table) >= self.rotate_after
            bytes_greater = sys.getsizeof(
                json.dumps(current_table)) >= self.rotate_after

            # rotate log files based on the number of log entries or logs size
            # in bytes
            if (self.rotate_units == RotateUnit.ENTRIES and entries_greater) or (
                    self.rotate_units == RotateUnit.BYTES and bytes_greater):
                rotation_path = self.next_rotation_file()
                logs.truncate()

        # create / update the log rotation file
        if rotation_path is not None:
            self._created_rotated(rotation_path, current_table)

    def _created_rotated(self, path, entries):
        """ Create the rotated log database with the given entries.
        """
        with TinyDB(path) as datastore:
            logs = datastore.table(self.table, cache_size=0)

            logs.truncate()
            logs.insert_multiple(entries)

    def next_rotation_file(self):
        """ Get the path of the next log rotation file to be written / overwritten.
        """
        next_file = ""
        for rotation in range(0, self.rotate_times):
            curr = f'{self.rotate_path}.{rotation}'
            if next_file == "" and os.path.exists(curr):
                # the previous rotation file is newer than this one,
                # thus this one should be overwritten
                if rotation != 0 and os.path.getmtime(curr) < os.path.getmtime(
                        f'{self.rotate_path}.{rotation - 1}'):
                    next_file = curr
                # the last rotation file exists, since we have checked if any
                # of the others are newer the first should be overwritten
                elif rotation == self.rotate_times - 1:
                    next_file = f'{self.rotate_path}.0'
            # the rotation file does not yet exist
            elif next_file == "":
                next_file = curr

        return next_file

@dataclass
class KeyedDB(BaseDB):
    """ NoSQL database with unique entries keyed on specific document field.

        Attributes:
            path: filesystem path for database storage
            table: set current table (can be changed using set_table)
            read_only: do not write to this database
            keys: fields to be checked as primary keys for each table (leave default)
            init_keys: fields to be checked as primary keys for the initial table
    """
    keys: Dict[str, List[str]] = field(default_factory=dict)
    init_keys: InitVar[List[str]] = None

    def __post_init__(self, init_keys):
        """ Automatically set keys for initial table.
        """
        self.keys = {}
        self.keys[self.table] = init_keys

    def set_table(self, table, table_keys=None): # pylint: disable=W0221
        """ Set the table to perform operations on.
            Specify the keys for the table if it does not exist.
        """
        self.table = table

        if table not in self.keys:
            if table_keys is None:
                raise MissingTableKeysError

            self.keys[table] = table_keys

    def insert(self, entry):
        """ Insert an entry in the database.
            The entry must contain unique values for the keys.
        """

        if [ key for key in self.keys[self.table] if key not in entry ]:
            raise MissingKeyError

        key_values = { key: entry[key] for key in self.keys[self.table] }
        if self.get_matches(key_values):
            raise KeyExistsError

        BaseDB.insert(self, entry)

    def insert_multiple(self, entries):
        """ Insert multiple entries in the database.
            The entry must contain unique values for the keys.
        """

        for entry in entries:
            if [ key for key in self.keys[self.table] if key not in entry ]:
                raise MissingKeyError

            key_values = { key: entry[key] for key in self.keys[self.table] }
            if self.get_matches(key_values):
                raise KeyExistsError

        BaseDB.insert_multiple(self, entries)

    def update(self, entry):
        """ Update an entry in the database with the given key values.
            Inserts the entry if it does not exist.
        """
        if [ key for key in self.keys[self.table] if key not in entry ]:
            raise MissingKeyError

        key_values = { key: entry[key] for key in self.keys[self.table] }

        updated = self.update_insert(entry, key_values)

    def get_entry(self, keys):
        """ Get an entry from the database with the given key values.
            Returns None if no entry is found.
        """
        if list(keys.keys()) != self.keys[self.table]:
            raise InvalidKeysError

        matches = self.get_matches(keys)

        if not matches:
            return None

        return matches[0]

    def delete_entry(self, keys):
        """ Delete an entry from the database with the given key values.
            Returns True if an entry was deleted.
        """
        if list(keys.keys()) != self.keys[self.table]:
            raise InvalidKeysError

        deleted = self.delete_matches(keys)

        if not deleted:
            return False

        return True

class ReadOnlyError(Exception):
    """ Exception to be thrown when a write action is attempted on a read-only database.
    """

class KeyExistsError(Exception):
    """ Exception to be thrown when an entry is added to a KeyedDB for which another entry
        with the same keys already exists.
    """

class MissingKeyError(Exception):
    """ Exception to be thrown when an entry is added to a KeyedDB if the entry does not
        contain the keys specified for the table.
    """

class MissingTableKeysError(Exception):
    """ Exception to be thrown when set_table is called on a KeyedDB for a new table and
        the keys parameter is empty.
    """

class InvalidKeysError(Exception):
    """ Exception to be thrown when a KeyedDB operation requiring keys is called with
        keys that do not match the current tables keys.
    """
