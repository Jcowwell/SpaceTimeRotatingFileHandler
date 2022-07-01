import os
import time
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Union, Optional

# SpaceTimeRotatingFileHandler
# NOTE: - Adopted from: 
# * "Write Header To A Python Log File, But Only If A Record Gets Written" : https://stackoverflow.com/a/33492520/6427171
# * "The Logging.Handlers: How To Rollover After Time Or Maxbytes?" : https://stackoverflow.com/a/6347764/6427171


class SpaceTimeRotatingFileHandler(RotatingFileHandler, TimedRotatingFileHandler):
    """
    Handler for logging to a file,  which switches from one file
    to the next when the current file reaches a certain size or at certain timed
    intervals.

    Inherits from RotatingFileHandler & TimedRotatingFileHandler

    Default Settings:
        * 25 MB limit
        * Rotates every week
        * Rotates up to 100 Backups

    If backupCount is > 0, when rollover is done, no more than backupCount
    files are kept - the oldest ones are deleted.
    """

    # Pass the file name and header string to the constructor.
    def __init__(self, filename: str,  mode: str='a', maxBytes: int=26209999, backupCount: int =100, encoding: Union[str, None]=None, delay: int=0, when: str='D', interval: int=7, utc: bool=False, header: Optional[str]=None, archive: bool=False):
        # Store the header information.
        self.header = header

        # Call the parent __init__
        RotatingFileHandler.__init__(
            self=self, filename=filename, mode=mode, maxBytes=maxBytes,
            backupCount=backupCount, encoding=encoding, delay=delay
        )

        TimedRotatingFileHandler.__init__(
            self=self, filename=filename, when=when, interval=interval, 
            backupCount=backupCount, encoding=encoding, delay=delay, utc=utc
        )

        # Write the header if delay is False and a file stream was created.
        if not delay and self.stream is not None and header is not None:
            self.stream.write('%s\n' % header)
    
    def doRollover(self) -> None:
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        dfn = self.rotation_filename(self.baseFilename + "." +
                                     time.strftime(self.suffix, timeTuple))
    
        if self.backupCount > 0:
            sfn = self.rotation_filename("%s.%03d" % (dfn, 1))
            rotation_number: int = 1
            while os.path.exists(sfn):
                sfn = self.rotation_filename("%s.%03d" % (dfn, rotation_number))
            self.rotate(self.baseFilename, sfn)
            for s in self.getFilesToDelete():
                os.remove(s)
        else:
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()
            if self.header is not None: # if a header is present, let's start the new file with it.
                print("Hi!")
                self.stream.write('%s\n' % self.header)

        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt

    def shouldRollover(self, record) -> int:
        return RotatingFileHandler.shouldRollover(self,record) or TimedRotatingFileHandler.shouldRollover(self,record=record)


