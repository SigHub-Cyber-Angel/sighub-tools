# SigHub logtail
[![Lint](https://github.com/SigHub-Cyber-Angel/sighub-tools/workflows/Lint%20logtail/badge.svg)](https://github.com/SigHub-Cyber-Angel/sighub-tools/actions?query=workflow%3ALint%20logtail)
[![Test](https://github.com/SigHub-Cyber-Angel/sighub-tools/workflows/Test%20logtail/badge.svg)](https://github.com/SigHub-Cyber-Angel/dashboard-backend/actions?query=workflow%3ATest%20logtail)
## Introduction
An asynchronous log tail event handler for use with the Twisted framework (twistedmatrix.com).
## Supported Python Versions
Unit tests are run for Python 3.7 - 3.9.
## Installation using pip
```
pip3 install git+https://github.com/SigHub-Cyber-Angel/sighub-tools.git#egg=sighub.logtail\&subdirectory=logtail
```
## Examples
```
>>> import logging
>>> from sighub.logtail import LogTail, TAIL_ROTATED
>>> 
>>> logging.basicConfig(level="INFO")
>>> 
>>> path = '/var/log/syslog'
>>> syslog_tail = None
>>> 
>>> def syslog_reader(line):
>>>     # do something with the log lines here
>>>     pass
>>> 
>>> def check_tails():
>>>     global syslog_tail
>>> 		
>>> if syslog_tail.state() == TAIL_ROTATED:
>>>     logging.info("rotating syslog reader")
>>>     syslog_tail.reset()
>>> 		
>>> def error_handler(error):
>>>     logging.error(error)
>>> 		
>>> def main():
>>>     global syslog_tail
>>> 		
>>>     logging.info("tailing syslog")
>>>     syslog_tail = logtail(path, syslog_reader, error_handler, reactor=reactor, full=True)
>>> 		
>>>     # check log tails to ensure they are still alive every 10 seconds
>>>     tails_task = task.loopingcall(check_tails)
>>>     tails_task.start(10)
>>> 		
>>>     logging.info("finished startup")
>>>     reactor.run()
>>> 		
>>> main()
```
