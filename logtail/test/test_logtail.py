import os
import unittest

from twisted.internet import reactor

from sighub.logtail import (
    LogTail,
    TAIL_ROTATED,
    TAIL_EXISTS
)

class LogTailTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            'TAIL_EXISTS': TAIL_EXISTS,
            'TAIL_ROTATED': TAIL_ROTATED,
            'TAIL_FULL': [
                '00:00:00 abcd\n',
                '00:01:00 efgh\n'
            ],
            'TAIL': [
                '00:02:00 ijkl\n',
            ]
        }
        self.input = {
            'TAIL': [
                '00:00:00 abcd\n',
                '00:01:00 efgh\n'
            ],
            'TAIL_APPEND': [
                '00:02:00 ijkl\n'
            ]
        }
        os.mkdir('tmp')

    def test_tail_exists(self):
        with open('tmp/tail_exists.log', 'w') as log:
            log.writelines(self.input['TAIL'])

        def _reader(line):
            pass

        def _handler(error):
            pass

        tail = LogTail('tmp/tail_exists.log', _reader, _handler, reactor=None, full=True)

        result = tail.state()
        self.assertEqual(self.expected['TAIL_EXISTS'], result, msg=f'state is not {self.expected.get("TAIL_EXISTS")}: {result}')

        
        os.unlink('tmp/tail_exists.log')

    def test_tail_rotated(self):
        with open('tmp/tail_rotated.log', 'w') as log:
            log.writelines(self.input['TAIL'])

        def _reader(line):
            pass

        def _handler(error):
            pass

        tail = LogTail('tmp/tail_rotated.log', _reader, _handler, reactor=None, full=True)

        # remove and replace the file
        os.unlink('tmp/tail_rotated.log')
        with open('tmp/tail_rotated.log', 'w') as log:
            log.writelines(self.input['TAIL'])

        result = tail.state()
        self.assertEqual(self.expected['TAIL_ROTATED'], result, msg=f'state is not {self.expected.get("TAIL_ROTATED")}: {result}')

        
        os.unlink('tmp/tail_rotated.log')

    def test_tail_full(self):
        with open('tmp/tail_full.log', 'w') as log:
            log.writelines(self.input['TAIL'])

        read = []
        def _reader(line):
            nonlocal read
            read.append(line)

        def _handler(error):
            pass

        tail = LogTail('tmp/tail_full.log', _reader, _handler, reactor=None, full=True)

        self.assertEqual(self.expected['TAIL_FULL'], read, msg=f'read is not {self.expected.get("TAIL_FULL")}: {read}')

        
        os.unlink('tmp/tail_full.log')

    def test_tail(self):
        with open('tmp/tail.log', 'w') as log:
            log.writelines(self.input['TAIL'])

        read = []
        def _reader(line):
            nonlocal read
            read.append(line)

        def _handler(error):
            pass

        tail = LogTail('tmp/tail.log', _reader, _handler, reactor=reactor, full=False)

        with open('tmp/tail.log', 'a') as log:
            log.writelines(self.input['TAIL_APPEND'])

        # make sure the reactor stops
        reactor.callLater(1, reactor.stop)

        # run the test using a real reactor
        reactor.run()

        self.assertEqual(self.expected['TAIL'], read, msg=f'read is not {self.expected.get("TAIL")}: {read}')

        
        os.unlink('tmp/tail.log')

    def tearDown(self):
        os.rmdir('tmp')
