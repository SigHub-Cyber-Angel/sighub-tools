import json
import os
import unittest

from sighub.jsondb import (
    BaseDB,
    LogDB,
    RotatingLogDB
)


class BaseDBTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            'ORIGINAL_TABLE': 'OrigTable',
            'SET_TABLE': 'SetTable',
            'ENTRY': {'a': 1, 'b': 2, 'c': 3},
            'MULTIPLE_ENTRY': [{'a': 1, 'b': 2}, {'a': 2, 'b': 1}],
            'GET_MATCHES': [{'a': 1, 'b': 2, 'c': 3}],
            'NEGATE_MATCHES': [{'a': 2, 'b': 2, 'c': 2}, {'a': 4, 'b': 1, 'c': 3}],
            'FIELD_IN': [{'a': 2, 'b': 2, 'c': 2}, {'a': 4, 'b': 1, 'c': 3}],
            'NEGATE_FIELD_IN': [{'a': 1, 'b': 2, 'c': 3}],
        }
        self.input = {
            'MATCH_DB': {
                'Matches': {
                    '1': {'a': 1, 'b': 2, 'c': 3},
                    '2': {'a': 2, 'b': 2, 'c': 2},
                    '3': {'a': 4, 'b': 1, 'c': 3}
                }
            }
        }
        os.mkdir('tmp')

    def test_set_table(self):
        db = BaseDB('tmp/base.db', self.expected['ORIGINAL_TABLE'], False)
        self.assertEqual(self.expected['ORIGINAL_TABLE'], db.table, msg=f'original table name is not {self.expected.get("ORIGINAL_TABLE")}: {db.table}')

        db.set_table(self.expected['SET_TABLE'])
        self.assertEqual(self.expected['SET_TABLE'], db.table, msg=f'set table name is not {self.expected.get("SET_TABLE")}: {db.table}')

        # no need to remove the database because we did not write any data (it
        # doesn't exist)

    def test_insert(self):
        db = BaseDB('tmp/insert.db', 'InsertTable', False)

        db.insert(self.expected['ENTRY'])
        all_entries = list(db.get_all())
        self.assertEqual([self.expected['ENTRY']], all_entries, msg=f'after insert all entries are not [ {self.expected.get("ENTRY")} ]: {all_entries}')

        os.unlink('tmp/insert.db')

    def test_insert_multiple(self):
        db = BaseDB('tmp/insert.db', 'InsertTable', False)

        db.insert_multiple(self.expected['MULTIPLE_ENTRY'])
        all_entries = list(db.get_all())
        self.assertEqual(self.expected['MULTIPLE_ENTRY'], all_entries, msg=f'after insert multiple all entries are not {self.expected.get("MULTIPLE_ENTRY")}: {all_entries}')

        os.unlink('tmp/insert.db')

    def test_get_matches(self):
        with open('tmp/matches.db', 'w') as f:
            json.dump(self.input['MATCH_DB'], f)

        db = BaseDB('tmp/matches.db', 'Matches', False)

        matches = list(db.get_matches({'a': 1, 'b': 2}))
        self.assertEqual(self.expected['GET_MATCHES'], matches, msg=f'get matches entries are not {self.expected.get("GET_MATCHES")}: {matches}')

        negated = list(db.get_matches({'a': 1, 'b': 2}, negate=True))
        self.assertEqual(self.expected['NEGATE_MATCHES'], negated, msg=f'negated get matches entries are not {self.expected.get("NEGATE_MATCHES")}: {negated}')

        os.unlink('tmp/matches.db')

    def test_get_field_in(self):
        with open('tmp/field_in.db', 'w') as f:
            json.dump(self.input['MATCH_DB'], f)

        db = BaseDB('tmp/field_in.db', 'Matches', False)

        matches = list(db.get_field_in('a', [2, 4]))
        self.assertEqual(self.expected['FIELD_IN'], matches, msg=f'field in entries are not {self.expected.get("FIELD_IN")}: {matches}')

        negated = list(db.get_field_in('a', [2, 4], negate=True))
        self.assertEqual(self.expected['NEGATE_FIELD_IN'], negated, msg=f'negated get field in entries are not {self.expected.get("NEGATE_FIELD_IN")}: {negated}')

        os.unlink('tmp/field_in.db')

    def tearDown(self):
        os.rmdir('tmp')


class LogDBTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            'ORIGINAL_TABLE': 'OrigTable',
            'SET_TABLE': 'SetTable',
            'ENTRY': {'ts': 1, 'a': 1, 'b': 2, 'c': 3},
            'MULTIPLE_ENTRY': [{'ts': 1, 'a': 1, 'b': 2}, {'ts': 2, 'a': 2, 'b': 1}],
            'GET_MATCHES': [{'a': 1, 'b': 2, 'c': 3}],
            'NEGATE_MATCHES': [{'a': 2, 'b': 2, 'c': 2}, {'a': 4, 'b': 1, 'c': 3}],
            'FIELD_IN': [{'a': 2, 'b': 2, 'c': 2}, {'a': 4, 'b': 1, 'c': 3}],
            'NEGATE_FIELD_IN': [{'a': 1, 'b': 2, 'c': 3}],
            'BEFORE': [{'a': 1, 'ts': 1}, {'a': 2, 'ts': 2}],
            'AFTER': [{'a': 4, 'ts': 4}, {'a': 5, 'ts': 5}],
            'BETWEEN': [{'a': 2, 'ts': 2}, {'a': 3, 'ts': 3}],
        }
        self.input = {
            'MATCH_DB': {
                'Matches': {
                    '1': {'a': 1, 'b': 2, 'c': 3},
                    '2': {'a': 2, 'b': 2, 'c': 2},
                    '3': {'a': 4, 'b': 1, 'c': 3}
                }
            },
            'TSLESS_ENTRY': {'a': 1, 'b': 2},
            'GET_ENTRIES': [
                    {'a': 1, 'ts': 1},
                    {'a': 2, 'ts': 2},
                    {'a': 3, 'ts': 3},
                    {'a': 4, 'ts': 4},
                    {'a': 5, 'ts': 5}
            ]
        }
        os.mkdir('tmp')

    def test_append(self):
        db = LogDB('tmp/append.db', 'AppendTable', False)

        db.append(self.expected['ENTRY'])
        all_entries = list(db.get_all())
        self.assertEqual([self.expected['ENTRY']], all_entries, msg=f'after append all entries are not [ {self.expected.get("ENTRY")} ]: {all_entries}')

        os.unlink('tmp/append.db')

    def test_append_multiple(self):
        db = LogDB('tmp/append.db', 'AppendTable', False)

        db.append_multiple(self.expected['MULTIPLE_ENTRY'])
        all_entries = list(db.get_all())
        self.assertEqual(self.expected['MULTIPLE_ENTRY'], all_entries, msg=f'after append multiple all entries are not {self.expected.get("MULTIPLE_ENTRY")}: {all_entries}')

        os.unlink('tmp/append.db')

    def test_add_timestamp(self):
        db = LogDB('tmp/timestamp.db', 'TimestampTable', False)

        db.append(self.input['TSLESS_ENTRY'])
        all_entries = list(db.get_all())
        for entry in all_entries:
            self.assertIn('ts', entry, msg=f'timestamp not found in {entry}')

        os.unlink('tmp/timestamp.db')

    def test_get_before(self):
        db = LogDB('tmp/before.db', 'BeforeTable', False)

        db.append_multiple(self.input['GET_ENTRIES'])

        before = db.get_before(3)
        self.assertEqual(self.expected['BEFORE'], before, msg=f'before entries are not {self.expected.get("BEFORE")}: {before}')

        os.unlink('tmp/before.db')

    def test_get_after(self):
        db = LogDB('tmp/after.db', 'AfterTable', False)

        db.append_multiple(self.input['GET_ENTRIES'])

        after = db.get_after(3)
        self.assertEqual(self.expected['AFTER'], after, msg=f'after entries are not {self.expected.get("AFTER")}: {after}')

        os.unlink('tmp/after.db')

    def test_get_between(self):
        db = LogDB('tmp/between.db', 'BetweenTable', False)

        db.append_multiple(self.input['GET_ENTRIES'])

        between = db.get_between(2, 3)
        self.assertEqual(self.expected['BETWEEN'], between, msg=f'between entries are not {self.expected.get("BETWEEN")}: {between}')

        os.unlink('tmp/between.db')

    def tearDown(self):
        os.rmdir('tmp')


class RotatingLogDBTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            'ROTATE': [
                {'a': 1, 'ts': 1},
                {'a': 2, 'ts': 2},
                {'a': 3, 'ts': 3},
                {'a': 4, 'ts': 4},
                {'a': 5, 'ts': 5}
            ]
        }
        self.input = {
            'ROTATE_ENTRIES': [
                {'a': 1, 'ts': 1},
                {'a': 2, 'ts': 2},
                {'a': 3, 'ts': 3},
                {'a': 4, 'ts': 4},
                {'a': 5, 'ts': 5}
            ]
        }
        os.mkdir('tmp')

    def test_rotate(self):
        db = RotatingLogDB('tmp/rotate.db', 'RotateTable',
                           False, 3, 3, 'tmp/rotate.db')

        db.append_multiple(self.input['ROTATE_ENTRIES'])

        rotated = LogDB('tmp/rotate.db.0', 'RotateTable', False)

        all_entries = list(rotated.get_all())
        self.assertEqual(self.expected['ROTATE'], all_entries, msg=f'rotated entries are not {self.expected.get("ROTATE")}: {all_entries}')

        os.unlink('tmp/rotate.db')
        os.unlink('tmp/rotate.db.0')

    def tearDown(self):
        os.rmdir('tmp')
