# Example usage #

assume your project has textid 'mytextid'

## simple indicator update create (minimalistic) ##

~~~
okerrclient -n delme -s OK 
~~~

## more complex example ##
~~~
okerrclient -i mytextid -n delme -s OK -S bzbzbz -u http://dev.okerr.com/okerr -m "numerical|minlim=0|maxlim=100" -v
~~~

## run API queries
configure `textid=mytextid` and `api-key = your_project_okerr_api_key` in `/etc/okerrclient.conf`.

~~~
okerrclient --api-indicators
okerrclient --api-indicator --name MyIndicator
okerrclient --api-filter sslcert '!policy:Default'
okerrclient --name MyIndicator --api-set url=http://google.com/ retest=1 
~~~

Or use in script (set policy 'Daily' for all 'whois' indicator with policy 'Default'): 
~~~shell
for i in `okerrclient --api-filter whois policy:Default`; 
do 
    echo fix $i; 
    okerrclient -i okerr --name $i --api-set policy=Daily; 
done
~~~
