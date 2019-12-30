#!/usr/bin/python

import os
import sys
import fasteners
# import contextlib
import time
import okerrclient
import traceback


# @contextlib.contextmanager
class pidfile:    

    def __init__(self, pidpath, lockpath=None, log=None):
    
        if lockpath is None:
            lockpath = pidpath + '.lock'
        
        self.lockpath = lockpath
        self.pidpath = pidpath
                
        self.logger = log
        self.lock = fasteners.InterProcessLock(self.lockpath, logger=log)
    
        
        
    def __enter__(self):
        #
        # MAGICAL LINE 
        # not working without this self.log(anything)
        #
        #self.log('{} locking {}'.format(os.getpid(), self.lock.path))
        
        # time.sleep(5)
        # self.log("{} pid enter".format(os.getpid()))        

                
        if self.lock.acquire(blocking=False):        
            # self.log("{} acquired lock {} {}".format(os.getpid(), self.lock.path, self.fileno()))
            pass
        else:
            self.log("{} failed to acquire lock".format(os.getpid()))
            raise okerrclient.OkerrLockError
        self.writepid()



    def writepid(self):
        #self.log("{} write pid".format(os.getpid()))
        # here we have an lock
        with open(self.pidpath,'w') as pf:
            pf.write(str(os.getpid())+'\n')
        
    def __exit__(self, etype, evalue, etb):
        if etype is not None and etype != SystemExit:
            self.log("{} etype: {}".format(os.getpid(),str(etype)))
            self.log("exception:"+etb.format_exc())
            self.log("traceback:"+traceback.extract_tb(etb))
        
        self.log("{} pid exit".format(os.getpid()))
        if self.lock.acquired:
            self.lock.release()
            os.unlink(self.lockpath)
            os.unlink(self.pidpath)

    def fileno(self):
        return self.lock.lockfile.fileno()
    
    def log(self,msg):
        if self.logger:
            self.logger.error(msg)
        
    def trylock(self):
        try:
            lock = fasteners.InterProcessLock(self.lockpath)
            if lock.acquire(blocking=False):
                lock.release()
                return True
        except Exception as e:
            pass
        return False        

if __name__ == '__main__':
    print("main ",sys.argv, len(sys.argv))
    
    if len(sys.argv)==2:
        pidname = sys.argv[1]
    else:
        pidname = '/tmp/test.pid'
    
    print("locking",pidname)
    try:
        with pidfile(pidname):            
            while(True):
                print("{} tick-tock".format(os.getpid()))
                time.sleep(1)        
    except okerrclient.OkerrLockError as e:
        print("lock error")
