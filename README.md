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
okerrclient --api-filter sslcert '!policy:Default'
okerrclient --name test --api-set url=http://google.com/ retest=1 
~~~
