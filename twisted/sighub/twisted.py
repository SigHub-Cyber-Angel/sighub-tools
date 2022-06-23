""" Wrapper functions and classes for common patterns used with
the Twisted framework (https://twistedmatrix.com).
"""
import logging

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
    def __init__(self, call, interval, log=True, now=False, exit_on_err=False, _clock=None):
        """ Create a started LoopingCall with error handling.

            @param call: the function to run at the given interval
            @param interval: the interval to run the function at in seconds
            @param log: whether to log caught errors or not
            @param now: whether to run call immediately or not
            @param exit_on_err: whether to stop the reactor when an error is caught or not
            @param _clock: for unit testing only

            @return LoopingCallStarter
        """
        self.loop_call = call
        self.interval = interval
        self.log = log
        self.now = now
        self.exit_on_err = exit_on_err
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

        if self.exit_on_err:
            _stop_running()
        elif not self.running:
            self._start()

def _stop_running():
    """ Stop the reactor if it is running.
    """
    # pylint: disable=no-member
    if reactor.running:
        # pylint: disable=no-member
        reactor.stop()
