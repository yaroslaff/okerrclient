import okerrclient.taskseq as ts
import psutil
import os
import types
import time
#import evalidate

from socket import AF_INET, AF_INET6, SOCK_STREAM, SOCK_DGRAM


class ProcTaskProcessor(ts.TaskProcessor):
    chapter = 'Processes'


class TaskUptime(ProcTaskProcessor):

    help = 'uptime in seconds'        
    
    #
    # convert seconds to days hours minutes seconds
    #
    def s2dhms(self,sec):
        s=""
        intervals = (
            ('d',86400),
            ('h',3600),
            ('m',60),
            ('s',1)
        )
    
        for suffix, num in intervals:
            if sec>num:
                c=sec/num
                s+="{}{} ".format(c,suffix)
                sec-=c*num
        return s
    
    
    def run(self,ts,data,args):
        bt = int(psutil.boot_time())        
        now = int(time.time())
        uptime = now-bt
#        ts.details = self.s2dhms(uptime)
        
        return uptime
        
TaskUptime('UPTIME',ts.TaskSeq)

class TaskLoadAvg(ProcTaskProcessor):

    help = 'load average'    
    
    
    defargs={
        'period': '0'
    }
        
    def run(self,ts,data,args):
        p = int(args['period'])
        ts.details = "{}, {}, {}".format(*os.getloadavg())
        
        return os.getloadavg()[p]
            
TaskLoadAvg('LOADAVG',ts.TaskSeq)



class TaskProcesses(ProcTaskProcessor):

    help = 'list of processes'    
    
    parse_args = False
    
    def run(self,ts,data,args):
        outdata = []
        count = 0
        attrs = ['name','exe','username','pid','create_time']
        for p in psutil.process_iter():
            try:
                ps={}
                for attr in attrs:
                    ps = p.as_dict(attrs=attrs)
                if 'exe' in ps and ps['exe']:
                    ps['basename']=os.path.basename(ps['exe'])
                ps['agesec'] = int( time.time() - ps['create_time'] )
                    
                outdata.append(ps)
            except psutil.NoSuchProcess:
                pass
                                   
        return outdata
TaskProcesses('PROCESSES',ts.TaskSeq)

class TaskConnections(ProcTaskProcessor):
    help = 'list of network connections'

    parse_args = False
    
#    defargs = {
#        'expr': 'proto=="tcp" and status=="LISTEN"',
#        'fmt': '{proto} {ip}:{port} {status} ({basename})', 
#        'ifmt': '{iname}:{proto}{port}', 
#        'single': '1'}

    def run(self,ts,data,args):
        data=list()

        outdata=[]
        
        proto_map = {
            (AF_INET, SOCK_STREAM): 'TCP',
            (AF_INET6, SOCK_STREAM): 'TCP6',
            (AF_INET, SOCK_DGRAM): 'UDP',
            (AF_INET6, SOCK_DGRAM): 'UDP6',
        }       

        # compile evalidate expression
    
        if False:        
            try:
                node = evalidate.evalidate(args['expr'])
                code = compile(node,'<usercode>','eval')            
            except ValueError as e:
                ts.oc.log.error('Error in filter expression:',e)
                return None
        
        count = 0

        first=True
        
        for p in psutil.process_iter():
            try:        
                conns = p.connections()
                if len(conns):
                    #print(p)
                    # print(conns)
                    
                    for c in conns:
                        # print(c)
                        cs = {}
                        # cs['iname']=ts.iname
                        cs['name']=p.name()
                        cs['pid']=p.pid
                        cs['basename']=os.path.basename(p.exe())
                        cs['exe']=p.exe()
                        cs['proto']=proto_map[(c.family,c.type)] 
                        cs['ip']=c.laddr[0]
                        cs['port']=c.laddr[1]
                        cs['status']=c.status
                                
                        outdata.append(cs)
         
            except (psutil.Error, psutil.AccessDenied, psutil.NoSuchProcess):
                pass
                
        return outdata

TaskConnections('CONNECTIONS',ts.TaskSeq)


