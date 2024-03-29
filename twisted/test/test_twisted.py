import json
import shutil
import unittest

# The tests are run from the twisted directory which contains sighub
# this overrides any sighub standard python libraries so capture
# needs to be added to the sighub library folder so we find it.
CAPTURE_SRC = '../capture/sighub/capture.py'
CAPTURE_DST = 'sighub/capture.py'
shutil.copy(CAPTURE_SRC, CAPTURE_DST)

from sighub.capture import Capture
from twisted.internet.task import Clock
from sighub.twisted import LoopingCallStarter, ReaderEventLoopWrapper

def dummy_call():
    pass

def error_call():
    raise Exception()

class ArgsUpdateChecker:

    def __init__(self):
        self.check = 0

    def inc(self):
        self.check += 1

def dummy_args_call(arg_1: ArgsUpdateChecker):
    arg_1.inc()

class LoopingCallStarterTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            'ARGS_INCREMENTED': 1,
            'INIT_CALL': dummy_call,
            'INIT_INTERVAL': 10,
            'INIT_LOG': True,
            'INIT_NOW': False,
            'INIT_EXIT': False,
            'INIT_RUNNING': True,
            'INIT_DUMP_PATH': None,
            'ERROR_RUNNING': True,
            'ERROR_ERRORS': [ '<twisted.python.failure.Failure builtins.Exception: >' ],
            'DUMP_LINE': '    raise Exception()',
            'EXIT_RUNNING': False,
            'EXIT_ERRORS': [ '<twisted.python.failure.Failure builtins.Exception: >' ],
            'EXIT_REACTOR_RUNNING': False,
            'KWARGS_INCREMENTED': 1,
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
        self.assertEqual(self.expected['INIT_DUMP_PATH'], new.dump_path, \
            msg=f'init object dump_path is not {self.expected.get("INIT_DUMP_PATH")}: {new.dump_path}')

    def test_args(self):
        # inject a clock in LoopingCallStarter before the LoopingCall is started
        clock = Clock()

        update_checker = ArgsUpdateChecker()
        new = LoopingCallStarter(dummy_args_call, 10, args=(update_checker,), log=False, _clock=clock)

        # trigger an args increment
        clock.advance(10)

        self.assertEqual(self.expected['ARGS_INCREMENTED'], update_checker.check, \
            msg=f'check is not {self.expected.get("ARGS_INCREMENTED")}: {update_checker.check}')

    def test_kwargs(self):
        # inject a clock in LoopingCallStarter before the LoopingCall is started
        clock = Clock()

        update_checker = ArgsUpdateChecker()
        new = LoopingCallStarter(dummy_args_call, 10, kwargs={"arg_1": update_checker}, log=False, _clock=clock)

        # trigger an args increment
        clock.advance(10)

        self.assertEqual(self.expected['KWARGS_INCREMENTED'], update_checker.check, \
            msg=f'check is not {self.expected.get("KWARGS_INCREMENTED")}: {update_checker.check}')

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

    def test_dump(self):
        dump_path = 'err.json'
        # inject a clock in LoopingCallStarter before the LoopingCall is started
        clock = Clock()
        new = LoopingCallStarter(error_call, 10, dump_path=dump_path, log=False, _clock=clock)

        # trigger error_call
        clock.advance(10)

        trace = None
        with open(dump_path, 'r') as dump_file:
            trace = json.load(dump_file)

        self.assertTrue('trace' in trace, \
            msg=f'trace key not found in dump path: {trace}')

        err_line = trace.get('trace').split('\n')[-3]

        self.assertEqual(self.expected['DUMP_LINE'], err_line, \
            msg=f'dump error line is not {self.expected.get("DUMP_LINE")}: {err_line}')

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

class ReaderEventLoopWrapperTests(unittest.TestCase):
    def setUp(self):
        self.input = {
            'CALLBACK': dummy_call,
            'IFACE': 'lo'
        }

    def test_add_reader(self):
        # create a capture
        test_capture = Capture(self.input['IFACE'], callback=self.input['CALLBACK'])

        # pass a reader instance to the capture as the event loop
        loop_wrapper = ReaderEventLoopWrapper()
        test_capture.set_event_loop(loop_wrapper)

        # enable the capture which calls ReaderEventLoopWrapper.add_reader
        test_capture.enable()

        self.assertEqual(test_capture._callback, loop_wrapper.callback,
            msg=f'wrapper callback is not {test_capture._callback}: {loop_wrapper.callback}')

        self.assertNotEqual(-1, loop_wrapper.fileno(),
            msg=f'wrapper fileno is -1: {loop_wrapper.fileno()}')

    def tearDown(self):
        pass
