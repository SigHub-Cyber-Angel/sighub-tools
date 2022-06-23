import unittest

from twisted.internet.task import Clock
from sighub.twisted import LoopingCallStarter

def dummy_call():
    pass

def error_call():
    raise Exception()

class LoopingCallStarterTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            'INIT_CALL': dummy_call,
            'INIT_INTERVAL': 10,
            'INIT_LOG': True,
            'INIT_NOW': False,
            'INIT_EXIT': False,
            'INIT_RUNNING': True,
            'ERROR_RUNNING': True,
            'ERROR_ERRORS': [ '<twisted.python.failure.Failure builtins.Exception: >' ],
            'EXIT_RUNNING': False,
            'EXIT_ERRORS': [ '<twisted.python.failure.Failure builtins.Exception: >' ],
            'EXIT_REACTOR_RUNNING': False,
            'OKAY_RUNNING': True,
            'OKAY_NOT_STARTTIME': None,
        }
        self.input = {
        }

    def test_new(self):
        new = LoopingCallStarter(dummy_call, 10)

        self.assertEqual(self.expected['INIT_CALL'], new.loop_call, \
            msg=f'init object loop_call is not {self.expected.get("INIT_CALL")}: {new.loop_call}')
        self.assertEqual(self.expected['INIT_INTERVAL'], new.interval, \
            msg=f'init object interval is not {self.expected.get("INIT_INTERVAL")}: {new.interval}')
        self.assertEqual(self.expected['INIT_LOG'], new.log, \
            msg=f'init object log is not {self.expected.get("INIT_LOG")}: {new.log}')
        self.assertEqual(self.expected['INIT_NOW'], new.now, \
            msg=f'init object now is not {self.expected.get("INIT_NOW")}: {new.now}')
        self.assertEqual(self.expected['INIT_EXIT'], new.exit_on_err, \
            msg=f'init object exit_on_err is not {self.expected.get("INIT_EXIT")}: {new.exit_on_err}')
        self.assertEqual(self.expected['INIT_RUNNING'], new.running, \
            msg=f'init object running is not {self.expected.get("INIT_RUNNING")}: {new.running}')

    def test_error(self):
        # inject a clock in LoopingCallStarter before the LoopingCall is started
        clock = Clock()
        new = LoopingCallStarter(error_call, 10, log=False, _clock=clock)

        # trigger error_call
        clock.advance(10)

        self.assertEqual(self.expected['ERROR_RUNNING'], new.running, \
            msg=f'running is not {self.expected.get("ERROR_RUNNING")}: {new.running}')
        self.assertEqual(self.expected['ERROR_ERRORS'], new.errors, \
            msg=f'errors is not {self.expected.get("ERROR_ERRORS")}: {new.errors}')

    def test_exit(self):
        # inject a clock in LoopingCallStarter before the LoopingCall is started
        clock = Clock()
        new = LoopingCallStarter(error_call, 10, log=False, exit_on_err=True, _clock=clock)

        # trigger error_call
        clock.advance(10)

        self.assertEqual(self.expected['EXIT_RUNNING'], new.running, \
            msg=f'running is not {self.expected.get("EXIT_RUNNING")}: {new.running}')
        self.assertEqual(self.expected['EXIT_ERRORS'], new.errors, \
            msg=f'errors is not {self.expected.get("EXIT_ERRORS")}: {new.errors}')
        self.assertEqual(self.expected['EXIT_REACTOR_RUNNING'], new.clock.running, \
            msg=f'reactor.running is not {self.expected.get("EXIT_REACTOR_RUNNING")}: {new.clock.running}')

    def test_okay(self):
        # inject a clock in LoopingCallStarter before the LoopingCall is started
        clock = Clock()
        new = LoopingCallStarter(dummy_call, 10, log=False, _clock=clock)

        # trigger error_call
        clock.advance(10)

        self.assertEqual(self.expected['OKAY_RUNNING'], new.running, \
            msg=f'running is not {self.expected.get("OKAY_RUNNING")}: {new.running}')
        self.assertNotEqual(self.expected['OKAY_NOT_STARTTIME'], new.starttime, \
            msg=f'starttime is {self.expected.get("OKAY_NOT_STARTTIME")}: {new.starttime}')

    def tearDown(self):
        pass
