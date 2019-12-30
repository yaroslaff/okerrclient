import os
import sys
import stat
import time
import hashlib
import psutil
import six
import json

#from os.path import isfile, isdir, join

import okerrclient.taskseq as ts

if six.PY2:
    # old 2.x python
    class PermissionError(Exception):
        pass

    class FileNotFoundError(Exception):
        pass


def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()


class FsTaskProcessor(ts.TaskProcessor):
    chapter = 'Filesystem'

class DirProc(FsTaskProcessor):
    help='filesystem subtree'
    defargs={'path': '', 'md5': '', 'sha1': '', 'sha256': '', 'mindepth': '0', 'maxdepth': '10', 'symlink': '0'}

    def getrec(self, path, args, depth, symlinks=[]):
        # print("! getrec:",path)
        out = []

        rec=dict()
        rec['path']=os.path.realpath(path)
        rec['basename']=os.path.basename(path)
        rec['type']="UNKNOWN"
        rec['depth']=depth

        s = os.lstat(path)

        rec['size']=s.st_size
        rec['atime']=int(s.st_atime)
        rec['ctime']=int(s.st_ctime)
        rec['mtime']=int(s.st_mtime)

        now = time.time()
        rec['aage']=int(now-s.st_atime)
        rec['mage']=int(now-s.st_mtime)
        rec['cage']=int(now-s.st_ctime)



        if stat.S_ISDIR(s.st_mode):
            rec['type']="DIR"
            # should we go deeper?

            if not args['maxdepth'] or int(args['maxdepth'])>depth:
                for basename in os.listdir(path):
                    fullname = os.path.join(path,basename)
                    subout = self.getrec(fullname,args,depth+1, symlinks)
                    out.extend(subout)

        elif stat.S_ISCHR(s.st_mode):
            rec['type']="CHR"
        elif stat.S_ISBLK(s.st_mode):
            rec['type']="BLK"
        elif stat.S_ISREG(s.st_mode):
            rec['type']="REG"
            if args['md5']:
               rec['md5'] = hashfile(open(path,'rb'), hashlib.md5())
            if args['sha1']:
               rec['sha1'] = hashfile(open(path,'rb'), hashlib.sha1())
            if args['sha256']:
               rec['sha256'] = hashfile(open(path,'rb'), hashlib.sha256())


        elif stat.S_ISFIFO(s.st_mode):
            rec['type']="FIFO"
        elif stat.S_ISLNK(s.st_mode):
            if args['symlink']=='0':
                rec['type']="LNK"
            else:

                target = os.path.realpath(path)

                if target in symlinks:
                    return []

                symlinks.append(target)
                return self.getrec(target ,args,depth+1, symlinks)
                return []

        elif stat.S_ISSOCK(s.st_mode):
            rec['type']="SOCK"

        if depth>=int(args['mindepth']):
            out.append(rec)
        return out


    def run(self,ts,data,args):
        self.ts = ts
        if not isinstance(data,list):
            data=[]
        if args['path']:
            try:
                data.extend(self.getrec(args['path'],args,0))
            except (IOError, OSError, PermissionError, FileNotFoundError) as e:
                self.ts.oc.log.debug("exception: {}".format(e))
                ts.stop()
                return None

        else:
            self.ts.oc.log.error('DIR requires path, e.g. DIR path=/var/log or DIR path=/var/log/mail.log')
        return data

DirProc('DIR',ts.TaskSeq)

class DFProc(FsTaskProcessor):
    help='free disk space'
    defargs={'path': ''}

    @staticmethod
    def usage2g(u):
        g=1024*1024*1024 # 1GB

        d={}

        d['total']=u.total
        d['used']=u.used
        d['free']=u.free

        d['totalg']=int(u.total/g)
        d['usedg']=int(u.used/g)
        d['freeg']=int(u.free/g)


        d['percent']=u.percent
        return d

    @staticmethod
    def inodes(d):
        st = os.statvfs(d['path'])

        d['inodes_total'] = st.f_files
        d['inodes_free'] = st.f_ffree
        if st.f_files:
            d['inodes_percent'] = ((st.f_files - st.f_ffree) * 100) / st.f_files
        else:
            d['inodes_percent'] = 0

    def run(self,ts,data,args):
        self.ts = ts

        if args['path']:
            u = psutil.disk_usage(args['path'])
            d = DFProc.usage2g(u)
            d['path']=args['path']
            DFProc.inodes(d)
            return d
        else:
            dflist=[]
            points=[]
            # generate mount points which we willl watch
            for p in psutil.disk_partitions():

                if p.device.startswith('/dev/loop'):
                    continue
                points.append(p.mountpoint)

            #
            # BUGFIX: openvz root simfs is not listed in points
            #
            if not points:
                points.append('/')

            for point in points:
                try:
                    u = psutil.disk_usage(point)
                    d = DFProc.usage2g(u)
                    d['path']=point
                    DFProc.inodes(d)
                    dflist.append(d)

                except OSError as e:
                    self.ts.oc.log.warn('Have no access to mount {}'.format(point))
            return dflist

DFProc('DF', ts.TaskSeq)

class DUProc(FsTaskProcessor):
    help='disk usage'
    defargs={
        'path': '',
        #'depth': '0',
        #'sep': '-'
        }

    def run(self,ts,data,args):
        total = 0
        for root, dirs, files in os.walk(str(args['path']), topdown=False):
            for f in files:
                filepath = os.path.join(root,f)
                try:
                    if os.path.isfile(filepath) and not os.path.islink(filepath):
                            total += os.path.getsize(filepath)
                except OSError as e:
                    pass
        return total

DUProc('DU', ts.TaskSeq)


class FileProc(FsTaskProcessor):
    help='Read file'

    store_argline='path'
    parse_args=False

    defargs={'path': ''}

    tpconf={
        'read': []
    }

    def run(self,ts,data,args):

        path = args['path']

        # check if path in whitelist

        if ts.oc.tpconf_enabled:
            if not '*' in self.tpconf['read']:
                if not path in self.tpconf['read']:
                    # error! cannot read this file!
                    tpconfline = 'Maybe try --tpconf {}:read={}'.format(self.code, path)
                    ts.stop("File {} is not allowed to read. Whitelist read files: {}. Maybe try: {} ?".format(path,self.tpconf['read'], tpconfline))
                    return None

        try:
            fh = open(path, encoding='utf-8', errors='surrogateescape')
        except IOError as e:
            ts.oc.log.error('Cannot read file \'{}\': {}'.format(path, e))
            ts.stop()
            return None

        return fh

FileProc('FILE',ts.TaskSeq)


class JFileProc(ts.TaskAlias):
    help='Read JSON file.'
    help_suffix='\tsee options for FILE method\n'

    store_argline='path'
    parse_args=False

    defargs={'path': ''}

    alias = ['FILE','MULTILINE','FROMJSON']

JFileProc('JFILE',ts.TaskSeq)



class SeqFileProc(ts.TaskAlias):
    help='Run script from text file.'
    help_suffix='\tsee options for FILE method\n'

    store_argline='path'
    parse_args=False

    defargs={'path': ''}

    # alias = ['FILE','LIST','MKSEQ']
    alias = ['FILE','LIST','MKSEQ']

SeqFileProc('SEQFILE',ts.TaskSeq)
