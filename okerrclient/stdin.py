import okerrclient.taskseq as ts
import sys

class InputProcessor(ts.TaskProcessor):
    chapter = 'Input processor'

class StdinProc(InputProcessor):
    help = 'input from stdin'

    def run(self,ts,data,args):
        data=sys.stdin.read()
        return data
              
StdinProc('STDIN',ts.TaskSeq)        
        

