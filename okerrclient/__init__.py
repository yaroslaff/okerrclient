#!/usr/bin/python

import requests
import sys
import os
import psutil
import json
import time
import re
import argparse
import configargparse

import logging
import logging.handlers

import evalidate

import socket
from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM


# urlparse for python 2 and 3
# from future.standard_library import install_aliases
# install_aliases()
from urllib.parse import urlparse, urljoin


import okerrupdate
import okerrclient.taskseq
import okerrclient.taskproc
import okerrclient.fs
import okerrclient.listcmd
import okerrclient.stdin
import okerrclient.run
import okerrclient.network

import okerrclient.exceptions

version='2.0.161 (no future)'

ver = version.split(' ')[0]


def myunicode(s, encoding=None):
    if sys.version_info >= (3, 0):
        # python 3, nothing to do
        return s
    else:
        return unicode(s, encoding)


def briefpage(s, sz=50):
    for ch in '\r\n\t':
        s = s.replace(ch,'.')
    return s


class OkerrClient:

    # TODO: implement list of caches including ~/.okerr-cache.json
    cachepath = '/usr/local/etc/okerr-cache.json'
#    url = 'https://cp.okerr.com/'
#    url_director = 'api/director/{textid}'
    url = None
    url_received = 0
    textid = None
    secret = None
    log = None
    cache = None
    prefix = None
    retry = False # retry updates forever if failed
    x = dict() # special headers

    errors = 0
    last_error = ''
    last_error_time = None
    client_ip = None

    cfgvars = ['secret','textid','url','keyuser','keypass','cachepath']

    def __init__(self,cfg=None):
        #print("init with cfg:",cfg)
        # default null log handler
        self.log = logging.getLogger()
        self.log.addHandler(logging.NullHandler())

        self.retry = False # default
        self.sleeptime = 10

        self.dry_run = False
        self.tpconf_enabled = True


        # self.surl = None # server url. None before got from director

        if cfg:
            for k in self.cfgvars:
                if k in cfg:
                    #print("set self.{} to {}".format(k,cfg[k]))
                    setattr(self,k,cfg[k])
                else:
                    setattr(self,k,None)

    def setlog(self,log):
        self.log = log
        if self.project:
            self.project.setlog(log)


    def make_parser(self, parser=None):
        cflist = ['~/.okerrclient.conf','/usr/local/etc/okerrclient.conf','/etc/okerr/okerrclient.conf','/etc/okerrclient.conf']

        hostname = socket.gethostname()
        if '.' in hostname:
            hostname = hostname.split('.')[0]

        if parser is None:
            parser = configargparse.ArgumentParser(description='okerr client. update/create indicators over HTTP.',
                formatter_class = argparse.RawDescriptionHelpFormatter, add_help=False, default_config_files = cflist)

        parser.add_argument('--name',dest='defname', help="default indicator name ('{}' used if not set)".format(hostname), default=hostname)
        parser.add_argument('--dry',action='store_true', help="dry run (for testing). indicators will not be updated", default=False)
        parser.add_argument('-i','--textid',metavar='TextID', dest='textid', help='project unique text id (not project name!)')
        parser.add_argument('-S','--secret', metavar='secret', dest='secret',help='optional secret')
        parser.add_argument('--url', metavar='url', dest='url', default="https://cp.okerr.com/", help='update url')
        parser.add_argument('--direct', default=False, action='store_true', help='Direct mode (not use director feature, just use --url)')
        parser.add_argument('--keyuser', help='username for accessing key', default="client")
        parser.add_argument('--keypass', help='password for accessing key', default="")
        parser.add_argument('--tpconf', nargs='*', metavar='CODE:key=value', help='change conf for task processors, e.g. RUN:enabled=1', default=None)

        return parser

    def read_config(self, filename='/etc/okerrclient.conf'):
        parser = self.make_parser()
        parser.add_argument('-c',dest='conf', is_config_file=True, default=filename, help='conf file name')

        args = parser.parse_known_args()
        self.set_args(args[0])

    def set_x(self, name, value):
        self.x[name] = value

    def set_arg(self, name, value):
        if name in ['secret', 'textid']:
            setattr(self, name, value)

        if name == 'textid':
            # self.surl = None # renew session url
            self.project = None

    def set_args(self, args):

        for argname in ['keyuser', 'keypass', 'defname', 'textid', 'url']:
            v = getattr(args, argname, None)
            if v is not None:
                uv = myunicode(v, 'utf-8')
                setattr(self, argname, uv)
            else:
                setattr(self, argname, None)

        if args.tpconf:
            for tpc in args.tpconf:

                if tpc == 'disable':
                    self.tpconf_enabled = False
                    continue

                # usual tpconf: CODE:key=value
                try:
                    (code, kv) = tpc.split(':', 1)
                    (k,v) = kv.split('=', 1)
                    # print("code: {} arg: {} value: {}".format(code,k,v))
                    okerrclient.taskseq.TaskSeq.tp[code].tpconfset(k,v)
                except Exception as e:
                    print(u'ERROR {} {}'.format(tpc,e))
                    self.log.error('Can not process argument tpconf: {}'.format(tpc))
                    sys.exit(1)

        if args.dry:
            self.dry()

        self.project = okerrupdate.OkerrProject(self.textid, secret = args.secret, url = args.url, direct = args.direct)

    def error(self, message):
        self.errors += 1
        self.last_error = message
        self.last_error_time = time.time()
        self.log.error(message)

    def runseq(self, sequence, name=None, method=None):

        self.log.debug("runseq {}: {}".format(name, sequence))

        okerrclient.taskseq.TaskSeq.oc = self

        try:
            if name is None:
                name = self.defname

            ts = okerrclient.taskseq.TaskSeq(name,sequence, method)
        except (okerrclient.exceptions.OkerrBadMethod, ValueError) as e:
            # dump to console, if no such method
            self.log.error(e)
            sys.exit(1)
        try:
            ts.run()
        except okerrclient.exceptions.OkerrExc as e:
            self.log.error(u'OKERR ERROR: {}'.format(e))
            return False
        return True


    def __str__(self):
        return ("OkerrClient object\n"
            "cache: {cachepath}\n"
            "url: {url}\n"
            "textid: {textid}\n"
            "secret: {secret}\n").format(
                cachepath=self.cachepath,
                url=self.url,
                textid=self.textid,
                secret=self.secret)

    def geturl(self):
        return self.project.geturl()

        if self.surl is None or (time.time() - self.url_received) > 300:
            durl = urljoin(self.url, u'/api/director/{}'.format(self.textid))
            try:
                r = requests.get(durl, timeout=5)
            except requests.exceptions.RequestException as e:
                self.log.error("ERROR! geturl connection error: {}".format(e))
                self.surl = None
                self.url_received = 0
                return None
            if r.status_code != 200:
                self.log.error("ERROR! status code: {} for dURL {}".format(r.status_code, durl))
                return None

            self.log.debug("got url {} from director {}".format(r.text.rstrip(), durl))
            self.surl = r.text.rstrip()
            self.url_received = time.time()
        self.log.debug("geturl: return {}".format(self.surl))
        return self.surl



    def setloglevel(self,lvl):
        self.log.setLevel(lvl)
        if self.project:
            self.project.setloglevel(lvl)

    def quiet(self):
        self.setloglevel(logging.CRITICAL)

    def verbose(self):
        self.setloglevel(logging.DEBUG)


    def dry(self,dry=True):
        self.dry_run = dry

    def load(self):
        self.loadcache()

    def loadcache(self, force=False):

        self.cache={}
        return

        # load cache if it's not loaded
        # init/load cache
        try:
            with open(os.path.expanduser(self.cachepath),"r") as f:
                cachejson = f.read()
                self.cache = json.loads(cachejson)
        except IOError:
            self.log.info('no cache, initialize')
            self.cache={}
        except ValueError as e:
            self.log.error('broken cache: {}, reinit'.format(e))
            self.cache={}


    def save(self):
        self.savecache()

    def savecache(self):

        return

        self.cache['saved']=time.time()

        try:
            with open(os.path.expanduser(self.cachepath),"w") as f:
                cachejson = json.dumps(self.cache, indent=4)
                f.write(cachejson)
        except PermissionError:
            self.log.debug('cannot save cache {}'.format(self.cachepath))
            print(self.cache)


    def setretry(self,retry):
        self.retry = retry

    def altkeypath(self,path):
        ntried=0

        for trypath in path.split('|'):
            try:
                ntried+=1
                self.log.debug('try key {}'.format(trypath))
                data = self.keypath(trypath)
                if data is not None:
                    return (data, trypath)
            except okerrclient.exceptions.OkerrNoKey:
                self.log.debug('no such key: {}'.format(trypath))
                pass

        # if we are here, then no auth problem, but no key
        raise okerrclient.exceptions.OkerrNoKey('Failed all {} keypath: {} (textid: {})'.format(ntried, path, self.textid))

    def keypath(self,path):

        url = self.geturl()

        if url is None:
            # error. already logged
            return

        if not self.textid:
            raise okerrclient.exceptions.OkerrNoTextID('No textid. Cannot get keys.')
            return None

        url = urljoin(url,u'getkeyval/{}/{}'.format(self.textid,path))

        auth=None

        if self.keyuser and self.keypath:
            auth=(self.keyuser,self.keypass)

        try:
            r = requests.get(url, auth=auth, timeout=5)
        except requests.exceptions.RequestException as e:
            raise okerrclient.exceptions.OkerrClientServer(e)

        # print(str(r.status_code))

        if r.status_code==200:
            if 'Client-IP' in r.headers:
                self.client_ip = r.headers['Client-IP']
            data = json.loads(r.text)
            return data

        elif r.status_code == 401:
            raise okerrclient.exceptions.OkerrKeyAuth('Authentication required for getting keypath \'{}\' on project textid \'{}\', keyuser \'{}\''.format(path,self.textid,self.keyuser))
            return None
        elif r.status_code == 404:
            raise okerrclient.exceptions.OkerrNoKey('no key {}',path)
        else:
            self.log.error('okerr getkeyval error {} \'{:.50}\' textid:{} {}'.\
                format(r.status_code,briefpage(r.text),self.textid,path))
            raise okerrclient.exceptions.OkerrClientServer('Server communication error {}: {:.50}'.format(r.status_code, briefpage(r.text)))
            return None
        return None



    def update(self, name,status, details=None,
        method=None, policy='Default', tags=None, error=None, origkeypath=None, keypath=None):


        if self.dry_run:
            self.log.debug('Do NOT update: dry run. {} = {}'.format(name, repr(status)))
            return

        i = self.project.indicator(name, method = method, policy = policy,
            tags=tags, error = error, origkeypath = origkeypath, keypath = keypath)


        while True:
            try:
                i.update(status, details = details)
            except okerrupdate.OkerrExc as e:
                if not self.retry:
                    raise okerrclient.exceptions.OkerrExc(str(e))
                else:
                    self.log.warning("Update failed (will retry): {}".format(str(e)))
            else:
                # updated without exceptions
                return



    def UNUSED_update(self,name,status, details=None, textid=None, secret=None,
        method=None, policy='Default', tags=None, error=None, origkeypath=None, keypath=None):

        if self.dry_run:
            self.log.debug('Do NOT update: dry run. {} = {}'.format(name, repr(status)))
            return

        textid = textid or self.textid
        tags = tags or list()
        secret = secret or self.secret

        if not textid:
            self.log.error('Do not update: no textid')
            return

        # fix name
        if name.startswith(':') and self.prefix is not None:
            name = self.prefix+name

        r = None

        url = self.geturl()

        if not url:
            self.log.error("cannot update, url not given!")
            raise okerrclient.exceptions.OkerrClientServer('cannot update, url not given')
            return

        if not url.endswith('/'):
            url+='/'

        url = url+'update'

        self.log.debug(u"update: {}:{} = {} ({}) url: {}".format(self.textid,name,status,details, url))


        if keypath is None:
            keypath=''

        if origkeypath is None:
            origkeypath=''


        payload={
            'textid': textid,
            'name':name,
            'status': str(status),
            'details': details,
            'secret': secret,
            'method': method,
            'policy': policy,
            'tags': ','.join(tags),
            'error': error,
            'keypath': keypath,
            'origkeypath': origkeypath}

        # process x
        for k, v in self.x.items():
            xname = "x_" + k
            payload[xname] = v

        if self.secret:
            secretlog="[secret]"
        else:
            secretlog="[nosecret]"
        start = time.time()


        preview = str(status)

        preview = re.sub('[\r\n]'," ", preview)

        if len(str(preview))>40:
            preview = str(preview)[:38]+".."
        else:
            preview = str(preview)


        stop = False
        success = False

        while not stop:
            try:
                r = requests.post(url, data=payload, timeout=5)
                if r.status_code == 200:
                    stop = True
                    success = True
                    self.log.info(u'okerr updated {} = {}'.\
                        format(name,preview))
                else:

                    self.log.error(u'okerr update error ({}) textid:{}, {}={} {}'.\
                        format(r.status_code,self.textid,name,preview,secretlog))

                    if self.retry:
                        pass
                        # not daemon mode, retry=false in daemon
                        #self.error('okerr update error ({}) textid:{}, {}={} {}'.\
                        #    format(r.status_code,self.textid,name,preview,secretlog))
                    else:
                        raise okerrclient.exceptions.OkerrClientServer(u'okerr update error {} \'{:.150}\' textid:{}, {}={} {}'.\
                            format(r.status_code,briefpage(r.text),self.textid,name,status,secretlog))

                self.log.debug(u'Request to URL {}:'.format(r.request.url))
                self.log.debug(r.request.body)

            except requests.exceptions.RequestException as e:
                raise okerrclient.exceptions.OkerrClientServer(u'okerr exception {} textid:{}, {}={} {}'.\
                    format(e,self.textid,name,status,secretlog))

            if self.retry:
                if not stop:
                    time.sleep(self.sleeptime)
            else:
                # if no retries, simulate succeess
                stop=True



        if r:
            self.log.debug(r.content)
        else:
            self.log.debug("no reply, check log")
        self.log.debug("took {} sec.".format(time.time() - start))

        return success



def pid2name(pid):
    for proc in psutil.process_iter():
        if proc.pid==pid:
            return proc.name()
    return ""

def getportstr(expr):
    ports=[]
    cc=[]

    if expr is None or expr=='':
        expr='True'

    AF_INET6 = getattr(socket, 'AF_INET6', object())

    proto_map = {
        (AF_INET, SOCK_STREAM): 'tcp',
        (AF_INET6, SOCK_STREAM): 'tcp6',
        (AF_INET, SOCK_DGRAM): 'udp',
        (AF_INET6, SOCK_DGRAM): 'udp6',
    }

    cc=[]

    for proc in psutil.process_iter():
        try:
            for c in proc.connections():
                if c.status=='LISTEN' or c.status=='NONE':
                    proto=proto_map[(c.family,c.type)]
                    crec = {}
                    crec['proto']=proto
                    crec['ip']=c.laddr[0]
                    crec['port']=c.laddr[1]
                    crec['name']=os.path.basename(proc.exe())

                    if not crec in cc:
                        cc.append(crec)
        except psutil.NoSuchProcess:
            pass

    node = evalidate.evalidate(expr)
    code = compile(node,'<usercode>','eval')

    for c in cc:
        if eval(code,{},c):
            clist=[c['name'],c['proto'],c['ip'],str(c['port'])]
            cstr=':'.join(clist)
            ports.append(cstr)
        else:
            pass

    return "\n".join(sorted(ports))


def getiarg(textid,name,iarg,secret,urlprefix='http://update.okerr.com/okerr/'):
    payload={'textid': textid, 'name':name,
        'secret': secret, 'argname': iarg}


    url = urlprefix+'getpub'

    try:
        r = requests.post(url, data=payload, timeout=5)
        if r.status_code==200:
            if not 'urlcontent' in cache:
                cache['urlcontent']={}
            cache['urlcontent'][url]=r.content
            return r.content
        else:
            log.error('okerr getiarg failed ({}): {}'.\
                format(r.status_code,r.content))
            try:
                cached = cache['urlcontent'][url]
                log.error('use cached value for url {} : {}'.format(url,cached))
                return cached
            except:
                log.error('no cache for url {}'.format(url))
                return ""

    except requests.exceptions.RequestException as e:
        log.info(u'okerr getiarg exception {}'.\
            format(e))
        try:
            cached = cache['urlcontent'][url]
            log.error('use cached value for url {} : {}'.format(url,cached))
            return cached
        except:
            log.error('no cache for url {}'.format(url))
            return ""



# do not use it, use okerrupdate OkerrProject and OkerrIndicator
class Indicator():
    name = None
    period = None
    oc = None
    started = None
    tags = None
    method = None
    secret = None

    def __init__(self, name, method = None, textid=None, tags = list(), secret = None, period = None, oc = None):
        self.name = name
        self.last = 0
        self.period = 600
        if oc:
            self.oc = oc
        else:
            self.oc = okerrclient.OkerrClient()
            self.oc.read_config()
        self.method = method or 'heartbeat'
        self.tags = tags or list()
        self.secret = secret
        self.period = period or 600
        self.textid = textid
        self.started = time.time()
        self.last_update = 0

    # indicator.update
    def update(self, status='OK', details=''):

        if time.time() <= self.last_update + self.period:
            # skip update. too early
            return

        self.oc.update(name=self.name,
            status = status,
            details = details,
            method=self.method,
            textid=self.textid,
            tags=self.tags)
        self.last_update = time.time()
