import okerrclient.taskseq as ts
import requests
import okerrclient.pyping as pyping

class NetworkTaskProcessor(ts.TaskProcessor):
    chapter = 'Network operations'

class GetUrl(NetworkTaskProcessor):
    help = 'get HTTP document'
    
    
    tpconf={
        'url': []
    }
    
    # store_argline='n'
    # parse_args=False

    defargs = {
        'url':'', 
        'redirect': '1',
        'verify': '1',
        'user': '',
        'pass': '',
        'timeout': '5',
        }
    
    def validate_url(self, ts, url):
        
        if not ts.oc.tpconf_enabled:
            # disabled checks
            return True
             
        if '*' in self.tpconf['url']:
            return True
        
        for prefix in self.tpconf['url']:
            if url.startswith(prefix):
                return True
        
        return False
        
    def run(self,ts,data,args):
        out = dict()

        url = args['url']
        
        
        if not self.validate_url(ts, url):
            ts.oc.error('URL {} not validated against {}'.format(url, self.tpconf['url']))
            ts.stop('Not allowed this url. Set tpconf GETURL:url={}'.format(url))
            return None
            
        if args['redirect'] == '1':
            redir = True
        else:
            redir = False

        if args['verify'] == '1':
            verify = True
        else:
            verify = False

        try:
            timeout = int(args['timeout'])
        except ValueError:
            ts.oc.error('Cannot parse timeout value {}'.format(repr(args['timeout'])))
            ts.stop('Bad timeout value')
            return None

        if args['user'] and args['pass']:
            auth = (args['user'], args['pass'])
        else:
            auth = None        

        try:        
            r = requests.get(url, allow_redirects = redir, verify = verify, auth = auth, timeout = timeout)        
        except requests.exceptions.RequestException as e:
            ts.stop('GETURL exception {} {}'.format(type(e), e))
            return None                         

        out['elapsed'] = r.elapsed.total_seconds()        
        for field in ['status_code', 'text']:
            out[field] = getattr(r,field, None)
        
        for header in r.headers:
            out['h_'+header] = r.headers[header]
        
        return out
        
GetUrl('GETURL',ts.TaskSeq)            


class Ping(NetworkTaskProcessor):
    help = 'Ping remote host'
        
    # store_argline='n'
    # parse_args=False

    defargs = {
        'host':'okerr.com', 
        'count': '3',
        'timeout': '1000'
        }

    def run(self,ts,data,args):
        out = dict()

        try:
            count = int(args['count'])
            timeout = int(args['timeout'])
            r = pyping.ping(hostname = args["host"], timeout = timeout, count=count)
        except Exception as e:
            ts.stop(e)
            return 

        ts.details = "{} ({}) rtt: {}/{}/{} lost: {}".format(r.destination, r.destination_ip, r.min_rtt, r.avg_rtt, r.max_rtt, r.packet_lost)
        
        for aname in ['destination', 'destination_ip', 'min_rtt', 'avg_rtt', 'max_rtt','packet_lost']:
            out[aname] = getattr(r,aname)
        
        return out


Ping('PING',ts.TaskSeq)
