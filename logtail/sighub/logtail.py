#!/usr/bin/python3

# pylint: disable=missing-docstring

import io, logging, os, time, traceback
from twisted.internet import inotify
from twisted.python import filepath

# log states
TAIL_ERROR = -1
TAIL_EXISTS = 0
TAIL_ROTATED = 1

class LogTail:
    """ Tail a log file asynchronously
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments
    def __init__(self, file_path, line_callback, error_callback, reactor=None, \
                    full=False, timeout=180):
        """
        @param file_path: the log file the be tailed
        @param line_callback: a function to process lines from the file
        @param error_callback: function to call with traceback in case of exception
        @param reactor: the reactor running this class
        @param full: read the full file on initialisation
        @param timeout: how long to wait to see if the file has rotated
        """
        self.force = False
        try:
            self.error_callback = error_callback
            self.callback = line_callback
            self.path = file_path
            self.timeout = timeout
            self.fpath = filepath.FilePath(file_path)

            self.reactor = reactor

            # listen for file change events
            self.notifier = inotify.INotify()

            # the file
            self.file = open(file_path)
            self.f_ino = os.stat(self.path).st_ino

            # read the entire file
            if full:
                self.file.seek(0)
                self.reader(None, None, inotify.IN_MODIFY)
            # start tail at the end of the file
            else:
                self.file.seek(0, io.SEEK_END)

            self.notifier.startReading()
            self.notifier.watch(self.fpath, callbacks=[self.reader])
        except: # pylint: disable=W0702
            logging.error(traceback.format_exc())

            # ensure state returns TAIL_ROTATED
            self.force = True

    def reset(self):
        """ reset this LogTail, should be called if state returns TAIL_ROTATED
        """
        try:
            self.notifier.stopReading()
            self.notifier.stopConsuming()
            self.notifier.connectionLost('reset')
        except: # pylint: disable=W0702
            # don't assume we had a notifier
            pass

        try:
            self.fpath = filepath.FilePath(self.path)

            self.notifier = inotify.INotify()

            self.file = open(self.path)
            self.f_ino = os.stat(self.path).st_ino

            self.notifier.startReading()
            self.notifier.watch(self.fpath, callbacks=[self.reader])
        except: # pylint: disable=W0702
            # ensure state returns TAIL_ROTATED
            self.force = True

    def state(self):
        """ get the state of this LogTail

            @return state: one of TAIL_ERROR|TAIL_EXISTS|TAIL_ROTATED
        """
        if self.force:
            self.force = False
            return TAIL_ROTATED

        try:
            # has the file changed (rotated for example)
            curr_ino = os.stat(self.path).st_ino

            # self.f_ctime will be set when reset is called
            if self.f_ino == curr_ino:
                return TAIL_EXISTS
        except: # pylint: disable=W0702
            return TAIL_ERROR

        return TAIL_ROTATED


    def reader(self, ignored, fpath, mask): # pylint: disable=W0613
        """ reader called when file is changed
        """
        try:
            # file moved (handle rotation)
            if mask == inotify.IN_MOVE_SELF:
                timeout = 0
                # wait for the file to become available again
                while not os.path.exists(self.path) and timeout < self.timeout:
                    time.sleep(1)
                    timeout += 1

                # the daemon should be checking state and resetting
                return

            if not os.path.exists(self.path):
                # the daemon should be checking state and resetting
                return

            line = self.file.readline()
            while line != '':
                # handle lines that have not been full written
                if not line.endswith('\n'):
                    # get the file position and the read length we need to rewind
                    curr_pos = self.file.tell()
                    offset = len(line)
                    # seek back to the beginning of the current line
                    self.file.seek(curr_pos-offset)

                    # escape the loop
                    line = ''
                else:
                    self.callback(line)

                    # read the next line
                    line = self.file.readline()
        except: # pylint: disable=W0702
            self.error_callback(traceback.format_exc())
