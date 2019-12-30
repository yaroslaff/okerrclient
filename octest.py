#!/usr/bin/python

import okerrclient

oc = okerrclient.OkerrClient()
oc.read_config()
oc.set_arg('textid','accomazzi')
oc.set_arg('secret','sj2S$*sd')
oc.runseq(name='SERVER:something', sequence = ['DETAILS sixty six and six','STR 66.6'], method='numerical|maxlim=30')

