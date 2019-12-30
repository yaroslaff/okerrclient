
import okerrclient.taskseq as ts
import sys

class LocalProcessor(ts.TaskProcessor):
    chapter = 'Local processors'

class HelloProc(LocalProcessor):
    help = 'example custom processor'

    def run(self,ts,data,args):
        return "Hello World!"              

print("loading okerrclient local processor")

HelloProc('HELLO',ts.TaskSeq)        
        

