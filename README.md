# Example usage #

assume your project has textid 'qweqwe'

## simple indicator update create (minimalistic) ##

assume recently was work with project qweqwe (-i qweqwe) and now it's cached

./okerr-client -n delme -s OK 

## more complex example ##
./okerr-client -i qweqwe -n delme -s OK -S bzbzbz -u http://update.okerr.com/okerr -m "numerical|minlim=0|maxlim=100" -v

## get key

./okerr-client -i qweqwe --getkey @path

## get list of keys
./okerr-client -i qweqwe --listkeys @path

e.g.

MYNAME=mycluster:server1

for test in `./okerr-client --listkeys @$MYNAME`
do
    ./okerr-client -i qweqwe
done


## NEW DOC

./okerr-client -s 'DIR path=/var/log' 'FILTER type=="REG"' 'SORT field=size' 'FORMAT {size}' LAST JDUMP

./okerr-client -i qweqwe -n delme --url http://localhost:8000/okerr -s OK

{
    "name": "{iname}:opentcp",
    "checkmethod": "streqd",
    "sequence": {
        "10": "CONNECTIONS",
        "20": "FILTER status=='LISTEN' and proto=='tcp' and basename != 'smtpd'",
        "30": "SORT field=port",
        "40": "FORMAT {proto}:{port} {basename}"
    }
}


cat data.json | ./okerr-client -s STDIN FROMJSON MKSEQ JDUMP

./okerr-client -i qweqwe -n delme --url http://localhost:8000/okerr -s 'KEYVAL lib:maxlog' MKSEQ 



# update DF with details and method
 
./okerr-client -i qweqwe -n AA -i qweqwe -s 'METHOD numerical maxlim=80' 'DF' 'FORK iname={iname}:{path}' 'DETAILS used {usedg}/{totalg} ({freeg} free)' 'FORMAT {percent}'



# make wheel, upload
1. write some cool feature
2. change version both in okerr-client and in setup.py
3. register (only once)
    
    python setup.py register
 
4. generate source distribution (optional?):
  
  python setup.py sdist

5. make wheel:

  python3 setup.py bdist_wheel

6. upload

  twine upload dist/*


