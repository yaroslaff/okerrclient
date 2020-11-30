# okerrclient

okerrclient is old client for [okerr](https://okerr.com/) network/host monitoring system ([okerr-dev git repo](https://github.com/yaroslaff/okerr-dev)).

Most (especially new) users should not need to use this okerrclient package and should use [okerrupdate](https://github.com/yaroslaff/okerrupdate) client instead (it's much newer, redesigned and simpler to use) but okerrclient has features to use [okerr API](https://okerr.readthedocs.io/en/latest/Dev/API.html) which is missed in small okerrupdate utilities.

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

## Other okerr resources
- [Okerr main website](https://okerr.com/)
- [Okerr-server source code repository](https://github.com/yaroslaff/okerr-dev/) 
- [Okerr client (okerrupdate) repositoty](https://github.com/yaroslaff/okerrupdate) and [okerrupdate documentation](https://okerrupdate.readthedocs.io/)
- [Okerrbench network server benchmark](https://github.com/yaroslaff/okerrbench)
- [Okerr custom status page](https://github.com/yaroslaff/okerr-status)
- [Okerr JS-powered static status page](https://github.com/yaroslaff/okerrstatusjs)
- [Okerr network sensor](https://github.com/yaroslaff/sensor)
- [Demo ISP](https://github.com/yaroslaff/demoisp) prototype client for ISP/hoster/webstudio providing paid okerr access to customers
