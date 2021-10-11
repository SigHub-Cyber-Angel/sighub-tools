""" A TinyDB wrapper (https://github.com/msiemens/tinydb) providing document based log
    database and configuration database functionality.
"""

from dataclasses import dataclass
from datetime import datetime

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
        """ Insert multiple entries in database.
        """
        if self.read_only:
            raise ReadOnlyError

        with TinyDB(self.path) as datastore:
            curr_table = datastore.table(self.table, cache_size=0)

            for entry in entries:
                curr_table.insert(entry)

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

    def get_field_in(self, field, values, negate=False):
        """ Get all entries if the field matches one of the given values.
        """
        entries = []
        with TinyDB(self.path) as datastore:
            curr_table = datastore.table(self.table, cache_size=0)

            query = Query()

            if negate:
                entries = curr_table.search(~ query[field].one_of(values))
            else:
                entries = curr_table.search(query[field].one_of(values))

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


class ReadOnlyError(Exception):
    """ Exception to be thrown when a write action is attempted on a read-only database
    """
