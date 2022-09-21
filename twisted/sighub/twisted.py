""" Wrapper functions and classes for common patterns used with
the Twisted framework (https://twistedmatrix.com).
"""
import json
import logging
import os

from twisted.internet import (
    reactor,
    task
)

class LoopingCallStarter(task.LoopingCall):
    """ Wrapper to start a LoopingCall from twisted.internet.task.
        Error handling automatically logs the error and restarts the task.
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments
    def __init__(self, call, interval, log=True, now=False,
                 exit_on_err=False, dump_path=None, _clock=None):
        """ Create a started LoopingCall with error handling.

            @param call: the function to run at the given interval
            @param interval: the interval to run the function at in seconds
            @param log: whether to log caught errors or not
            @param now: whether to run call immediately or not
            @param exit_on_err: whether to stop the reactor when an error is caught or not
            @param dump_path: where to write an error dump on error
            @param _clock: for unit testing only

            @return LoopingCallStarter
        """
        self.loop_call = call
        self.interval = interval
        self.log = log
        self.now = now
        self.exit_on_err = exit_on_err
        self.dump_path = dump_path
        self.errors = []

        # initialize LoopingCall
        super().__init__(call)

        if _clock is not None:
            self.clock.callLater = _clock.callLater
        # start the loop
        self._start()

    def _start(self):
        """ Start the looping call. This is called on instantiation.

            @return deferred: deferred object returned by LoopingCall.start
        """
        self.loop_deferred = super().start(self.interval, now=self.now)
        self.loop_deferred.addErrback(self._errback)

        return self.loop_deferred

    def _errback(self, err):
        """ errback function automatically attached to the deferred in the start function.
            If log is set err is written to logging.error.
            If exit_on_err is set reactor.stop is called.

            @param err: the error being caught
        """
        self.errors.append(repr(err))

        if self.log:
            logging.error(err)

        # dump the error to a file if a dump path has been specified
        if self.dump_path is not None:
            if os.path.exists(self.dump_path):
                os.unlink(self.dump_path)
            info = { 'trace' : f'{err.getTraceback()}' }

            with open(self.dump_path, 'w') as dump_file:
                json.dump(info, dump_file)

        if self.exit_on_err:
            stop_running()
        elif not self.running:
            self._start()

class ReaderEventLoopWrapper():
    """ Wrapper converting an asyncio event_loop.add_reader call to
        reactor.addReader compatible class.

        Examples

        Use sighub.capture as a twisted reader:
        from twisted.internet import reactor
        import dpkt

        from sighub.capture import Capture
        from sighub.twisted import ReaderEventLoopWrapper, stop_running

        def print_packets(data):
            # print the IP protocol layer
            eth = dpkt.ethernet.Ethernet(data)
            print(repr(eth.data))

        def main():
            # create a capture
            cap = Capture('eth0', callback=print_packets, on_stop=stop_running)
            # pass a reader instance to the capture as the event loop
            cap.set_event_loop(ReaderEventLoopWrapper())

            # enable the capture which calls ReaderEventLoopWrapper.add_reader
            cap.enable()

            # add the capture event loop (instance of ReaderEventLoopWrapper) as a reader
            reactor.addReader(cap.event_loop)

            # start the twisted reactor
            reactor.run()
    """

    def __init__(self):
        """ Initialise object internals.
        """
        self.callback = None
        self.socket_fd = None

    # pylint: disable=invalid-name
    def doRead(self):
        """ Simply calls the callback.
        """
        self.callback()

    def add_reader(self, fileno, callback):
        """ Make add_reader reactor.addReader compatible.

            @param fileno: the integer representation of a PF_PACKET, SOCK_RAW socket fd
            @param callback: function to call on read (should handle socket.recv)
        """

        # set socket fileno
        self.socket_fd = fileno

        # set callback to be used in doRead
        self.callback = callback

    def fileno(self):
        """ The file descriptor to be read.
        """
        return self.socket_fd

    def connectionLost(self, reason):
        """ Do nothing if the connection is lost.
        """

    # pylint: disable=useless-option-value
    # pylint: disable=no-self-use
    # pylint: disable=invalid-name
    def logPrefix(self):
        """ Log prefix for this reader.
        """
        return 'ReaderEventLoopWrapper'

def stop_running():
    """ Stop the reactor if it is running.
    """
    # pylint: disable=no-member
    if reactor.running:
        # pylint: disable=no-member
        reactor.stop()
