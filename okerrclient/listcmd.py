import okerrclient.taskseq as ts
import string
import evalidate
import re
import shlex
import sys
import six
import json

from okerrclient.exceptions import OkerrBadMethod, OkerrBadData

class ListTaskProcessor(ts.TaskProcessor):
    chapter = 'Lists and Lists of dicts'

class FirstTaskProcessor(ListTaskProcessor):
    help = 'extract first element from list'
    
    store_argline='n'
    parse_args=False

    defargs = {'n':'1'}
        
    def run(self,ts,data,args):
        try:
            if isinstance(data,list):
                if int(args['n'])==1:
                    return data[0]
                else:
                    return data[:int(args['n'])]
            else:
                ts.stop()
                return None
        except IndexError:
            ts.stop()
            return None
        return None

FirstTaskProcessor('FIRST',ts.TaskSeq)            


class LastTaskProcessor(ListTaskProcessor):
    help = 'extract last element from list'
    store_argline='n'
    parse_args=False

    defargs = {'n':'1'}


    def run(self,ts,data,args):
        try:
            if isinstance(data,list):
                if int(args['n'])==1:
                    return data[-1]
                else:
                    pos = int(args['n'])
                    return data[-pos:]
            else:
                ts.stop()
                return None
        except IndexError:
            ts.stop()
            return None
        return None

LastTaskProcessor('LAST',ts.TaskSeq)            



class List2TextProc(ListTaskProcessor):
    help = 'list to multiline'

    def run(self,ts,data,args):
        outstr=''
        
        try:
            for s in data:
                if outstr:
                    outstr+='\n'
                outstr+=str(s)
            return outstr
        except TypeError:
            raise OkerrBadData('MULTILINE: TypeError. Must be iterable, got {}: {}'.format(type(data),repr(data)))
        
List2TextProc('MULTILINE',ts.TaskSeq)        
        
class LenProc(ListTaskProcessor):
    help = 'Length of list'
    parse_args = False

    def run(self,ts,data,args):
        if data is not None:
            return len(data)
        return None
                
LenProc('LEN',ts.TaskSeq)        


class TopProc(ListTaskProcessor):
    help = 'returns first N elements from list'
    store_argline='n'
    parse_args=False

    defargs = {'n':'1'}
    
    def run(self,ts,data,args):
        if not isinstance(data,list):
            return None
        
        return data[:int(args['n'])]
# TopProc('TOP',ts.TaskSeq)
    


class RevProc(ListTaskProcessor):
    help = 'reverse list'
    
    def run(self,ts,data,args):
        if not isinstance(data,list):
            return None
        
        return list(reversed(data))
        
RevProc('REV',ts.TaskSeq)



class ListProc(ListTaskProcessor):
    help = 'generate list from space-separated items or from input'
    store_argline='list'
    parse_args=False
    
    defargs = {
        'list': ''
    }
    
    def run(self,ts,data,args):
        if args['list']:            
            return shlex.split(args['list'])
        if data:
            return [ l for l in data ]
        return None
                
ListProc('LIST',ts.TaskSeq)




#
# looks for regex in string and replace it
# if data is dict, then string is taken from field by arg field
# if data is list, then each element (string or dict) processed
#
#

class ReplaceProc(ListTaskProcessor):
    help = 'Regexp replace'
    
    defargs = {
        'field': '',
        'search': '',
        'replace': '',
        'dest': ''
    }
    
    def run(self,ts,data,args):
        regex = re.compile(args['search'])

        if args['dest']:
            dest = args['dest']
        else:
            dest = args['field']

        
        if isinstance(data, six.string_types):
            return regex.sub(args['replace'],data)
        
        
        if isinstance(data,list):
            outlist=[]
            for row in data:
                if isinstance(row, six.string_types):
                    outlist.append(regex.sub(args['replace'],row))
                if isinstance(row, dict):
                    d = row.copy()                    
                    if args['field'] in row:                        
                        d[dest] = regex.sub(args['replace'],row[args['field']])
                    outlist.append(d)
            return outlist

        if isinstance(data, dict):
                        
            if args['field'] in data:                        
                data[dest] = regex.sub(args['replace'],data[args['field']])
            return data

        ts.oc.log.error("unreachable code in {}, bad data type: {}".format(self.code, type(data)))
        ts.stop()
            
        return None                
ReplaceProc('REPLACE',ts.TaskSeq)






#
# FORMAT
# dict
# in data: {'aaa': 'a-value', 'bbb': 'b-value}
# format: 'aaa is $aaa'
# out data: 'aaa is a-value'
#
# list of dict makes list of strings
#


class FormatProc(ts.FormatTaskProcessor):
    help = 'Convert list of dicts to list of strings'

    store_argline='format'
    parse_args=False

    defargs = {
        'format': '<no format given>',
    }

    def run(self,ts,data,args):
        outlist=[]
                
        fmt=args['format']
        try:
            etpl = string.Template(fmt)            
                #e = etpl.safe_substitute(v)            
           
            if data is None:
                return None
            
            if isinstance(data,six.string_types):               
                ts.stop()
                return None

            # list of dicts
            if isinstance(data,list):        
                for row in data:
                    rowstr = etpl.safe_substitute(row)                
                    outlist.append(rowstr)
                return outlist

            # dict
            if isinstance(data,dict):
                dstr = etpl.safe_substitute(data)
                return dstr
                
                
        except TypeError as e:
            ts.oc.log.error(u'exception in {}: {}'.format(self.code, e))
            ts.oc.log.error("format:"+str(fmt))
            ts.oc.log.error("data:"+str(data))            
            return None

                
FormatProc('FORMAT',ts.TaskSeq)        


class StripProc(ts.FormatTaskProcessor):
    help = 'Strip special chars from strings'

#    store_argline='format'
#    parse_args=False

    defargs = {
        'chars': '\r\n\t '
    }

    def run(self,ts,data,args):
        chars = args['chars']
        
        if isinstance(data, six.string_types):
            return data.strip(chars)

        # assume list, but catch exceptions!        
        outlist=[]
        try:
            for l in data:
                outlist.append(l.strip(chars))
            return outlist
        except:            
            ts.oc.log.error('{}: Unexpected data ({}): {}'.format(self.code, type(data), str(data)[:100]))
            ts.stop()
            return None
                
StripProc('STRIP',ts.TaskSeq)        
        

class CutProc(ts.FormatTaskProcessor):
    help = 'Convert list of dicts to list of strings'

#    store_argline='format'
#    parse_args=False

    defargs = {
        'sep': '',
        'start': '',
        'stop': ''
    }

    def run(self,ts,data,args):
        sep = args['sep']
        start = args['start']
        stop = args['stop']        
        
        if start:
            start = int(start)
        else:
            start=None
            
        if stop:
            stop=int(stop)
        else:
            stop=None
            
        
        if isinstance(data,six.string_types):
            if sep:
                data = re.split(sep,data)
            return data[start:stop]
        else:
            # probably we have list
            outlist = []
            for l in data:
                outlist.append( self.run(ts,l,args) )
            return outlist
            
        return None
                
CutProc('CUT',ts.TaskSeq)        
        
class ListFilterProc(ListTaskProcessor):
    help = 'Filter lists, leave only rows matching expression'

    store_argline='expr'
    parse_args=False

    defargs = {
        'expr': 'True',
    }

    def run(self,ts,data,args):
        outdata = []              
        if not isinstance(data,list):
            ts.oc.log.error('input data for FILTER is not list')
            return None        
            
        try:
            node = evalidate.evalidate(args['expr'])
            code = compile(node,'<usercode>','eval')            
        except (ValueError, SyntaxError) as e:
            raise OkerrBadMethod('Error in filter expression: {}'.format(e))
    
        for row in data:
            if eval(code, {}, row):
                outdata.append(row)

        return outdata
            
ListFilterProc('FILTER',ts.TaskSeq)        



        
class ListGroupProc(ListTaskProcessor):
    help = 'GROUP by field'

    store_argline=False
    parse_args=True

    defargs = {
        'key': '',
        'count': '',
        'min': '',
        'max': '',
    }

    def run(self,ts,data,args):
        outlist=[]
        d={}
        counters={}
        
        for row in data:
            try:
                keyfield = args['key']                
                key=row[keyfield]

                if key in d:                                  
                    # merge records
                    if args['min']:
                        f=args['min']
                        if row[f] < d[key][f]:
                            d[key] = row
                    elif args['max']:   
                        f=args['max']
                        if row[f] > d[key][f]:
                            d[key] = row                                             
                else:
                    d[key] = row            

                if args['count']:
                    if not key in counters:
                        counters[key] = 0
                    counters[key] += 1

                
            except KeyError:
                pass                    

        # now add counter
        for key in counters.keys():
            d[key][args['count']] = counters[key]
                    
        # convert dict to outlist
        
        outlist = list(d.values())
        
        return outlist
            
            
ListGroupProc('GROUP',ts.TaskSeq)        


class ListGrepProc(ListTaskProcessor):
    help = 'Filter list of dictionaries by regex'


    defargs = {
        're': '',
        'field': '',
        'inverse': '0',
        'ignorecase': ''
    }
    
    def run(self,ts,data,args):
        outdata=[]
        field = args['field']
        inverse = int(args['inverse'])
        restr = args['re']
        
        if args['ignorecase']:
            regex = re.compile(restr, re.IGNORECASE)
        else:
            regex = re.compile(restr)
        
        for row in data:
            if isinstance(row,dict):
                if field in row and regex.search(row[field]):
                    if inverse==0:
                        outdata.append(row)
                else:
                    if inverse==1:
                        outdata.append(row)
            elif isinstance(row,six.string_types):
                if regex.search(row):
                    if inverse==0:
                        outdata.append(row)
                else:
                    if inverse==1:
                        outdata.append(row)
        return outdata

ListGrepProc('GREP',ts.TaskSeq)        


class ListReqFieldsProc(ListTaskProcessor):
    help = 'Filter lists, leave only rows which are dicts having all listed fields'

    store_argline='fields'
    parse_args=False

    defargs = {
        'fields': '',
    }

    def run(self,ts,data,args):
        outdata = []              
        if not isinstance(data,list):
            ts.oc.log.error('input data for REQFIELD is not list')
            return None        
        
        for row in data:
            fail=False
            for rf in args['fields'].split(' '):
                if not rf in row:
                    fail=True
            if not fail:
                outdata.append(row)

        return outdata
            
ListReqFieldsProc('REQFIELDS',ts.TaskSeq)        

class ListOnlyFieldsProc(ListTaskProcessor):
    help = 'Delete all fields from dicts in list except only listed as arguments'

    store_argline='fields'
    parse_args=False

    defargs = {
        'fields': '',
    }

    def run(self,ts,data,args):
        outdata = []              
        if not isinstance(data,list):
            ts.oc.log.error('input data for REQFIELD is not list')
            return None        
        
        for row in data:
            fail=False
            outrow={}            
            for rf in args['fields'].split(' '):
                outrow[rf]=row[rf]
            outdata.append(outrow)

        return outdata
            
ListOnlyFieldsProc('ONLYFIELDS', ts.TaskSeq)        

class ListSumProc(ListTaskProcessor):
    help = 'Sum field value'

    store_argline='field'
    parse_args=False

    defargs = {
        'field': '',
    }

    def run(self,ts,data,args):
        outdata = 0              
        if not isinstance(data,list):
            ts.oc.log.error('input data for REQFIELD is not list')
            return None        
        
        for row in data:
            if isinstance(row, dict):
                outdata += float(row[args['field']])
            elif isinstance(row,six.string_types):
                outdata += float(row)
            
        return outdata
            
ListSumProc('SUM', ts.TaskSeq)        



class ListForkProc(ListTaskProcessor):
    help = 'fork each list element (dictionary or string) to separate indicator'
#    defargs = { 'name': '$_name:$_nfork' }
    defargs = {}

    def run(self,ts,data,args):
        nfork=0
        for row in data:
            if isinstance(row,dict):
                newrow = row.copy()
            else:
                newrow = row
                
            newts = ts.fork(ts.iname,ts.route,ts.method).run(newrow)            
            ts.stop()
        return None

#            if isinstance(row,dict):
#                d = ts.getvars()
#                d.update(row)
#            elif isinstance(row,six.string_types):
#                d = ts.getvars()
#                d['_str']=row                

#            d['_nfork']=nfork
            
            
#            newname = args['name'].format(**d)
            
#            etpl = string.Template(args['name'])            
#            newname = etpl.safe_substitute(d)            

                        
#            newts = ts.fork(newname,ts.route,ts.method)
#            newts = ts.fork(ts.iname,ts.route,ts.method)
#            newts.run(row)
            
#            nfork+=1
            
#            ts.stop()
            
        return None

ListForkProc('FORK', ts.TaskSeq)


