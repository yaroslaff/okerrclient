# from __future__ import print_function

import okerrclient.taskseq as ts
import sys
import pwd
import getpass
import os
import subprocess
import shlex

class RunTaskProcessor(ts.TaskProcessor):
    chapter = 'External programs processor'


class TaskRun(RunTaskProcessor):
    help = 'run program'

    parse_args=False
    store_argline='prog'


    defargs = {
        'prog': '',
    }

    tpconf = {
        'user': 'nobody',
        'safebin': []
    }

    def run(self,ts,data,args):               

        def mysuid(user):
            # override basic env variables
            os.environ['HOME']=user.pw_dir
            os.environ['SHELL']=user.pw_shell
            os.setuid(user.pw_uid)
            
        callarg = shlex.split(args['prog'])
        
        # is this program allowed?
        if ts.oc.tpconf_enabled:
            if not ('*' in self.tpconf['safebin'] or callarg[0] in self.tpconf['safebin']):
                ts.stop('{} is not in safebin: {}. Maybe try --tpconf {}:safebin={}'.format(callarg[0], str(self.tpconf['safebin']), self.code,callarg[0] ))
                #ts.stop()            
                return None

        try:
            user = pwd.getpwnam(self.tpconf['user'])            
        except KeyError:
            ts.oc.log.error('no such user {}'.format(self.tpconf['user']))
            ts.stop()            
            return None

     
        if os.geteuid() != 0:
            # not root!
            if user.pw_uid != os.geteuid():
                ts.oc.log.error('Current user {} (uid:{}) is not root and cannot swith to user \'{}\''.format(
                    getpass.getuser(),os.geteuid(), self.tpconf['user']))
                ts.stop()
                return

        try:               
            p = subprocess.Popen(callarg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn = lambda: mysuid(user))
        except OSError as e:
            # report problem
            ts.oc.log.error('Cannot run {} ({}). May be {} is not installed?'.format(str(callarg),e, callarg[0]))
            ts.stop()
            return None
            
        p.wait()
        res = p.communicate()
        
        out = dict()
        
        out['stdout']=res[0].decode('utf8')
        out['stderr']=res[1].decode('utf8')
        out['code']=p.returncode

        #if p.returncode or res[1]:
        #    ts.oc.log.error('error code: {}, stderr: {}'.format(p.returncode, res[1]))
        #    ts.stop()            
        #    return None            
        #return res[0].split('\n')
        return out
                
TaskRun('RUN', ts.TaskSeq)

        

