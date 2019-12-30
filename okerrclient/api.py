import requests
# import urlparse
import os
import sys
import logging
import json
from okerrclient import version
from okerrclient.exceptions import OkerrExc, OkerrAuth

# urlparse for python 2 and 3
# from future.standard_library import install_aliases
# install_aliases()
from urllib.parse import urlparse, urljoin

class okerrclient_api():
    def __init__(self, textid=None):
        self.base_url = 'https://cp.okerr.com/'
        self.api_url = None
        self.log = self.openlog()
        self.api_user = None
        self.api_pass = None
        self.api_key = None
        self.textid = textid
        self.http_auth = None
        self.headers = {
            'User-Agent': 'OkerrClient/{}'.format(version)
        }

    # add API arguments to parser
    def make_parser(self, parser):
        parser_apir = parser.add_argument_group('API commands (reading)')
        parser_apir.add_argument('--api-director', default=None, const='', nargs='?', help='get server for project')
        parser_apir.add_argument('--api-indicator', action='store_true', help='get JSON for 1 indicator')
        parser_apir.add_argument('--api-indicators', metavar='prefix', default=None, const='', nargs='?', help='list indicators by prefix')
        parser_apir.add_argument('--api-filter', metavar='filter', dest='api_fltr', default=None, nargs='+', help='filter. e.g.: host=google.com sslcert \'!maintenance\'')
        # parser_apir.add_argument('--api-tags', metavar='tags', default=None, nargs='+', help='tags (for tagfilter)')
        # parser_apir.add_argument('--api-notags', metavar='tags', default=None, nargs='+', help='tags (for tagfilter) for negative filtering')
        parser_apir.add_argument('--api-get', metavar='argument', default=None, help='get one argument of indicator')
        parser_apir.add_argument('--api-checkmethods', action='store_true', help='show checkmethods information')




        parser_apiw = parser.add_argument_group('API commands (writing)')
        parser_apiw.add_argument('--api-create', action='store_true', help='create indicator by name (with default checkmethod, all options and arguments)')
        parser_apiw.add_argument('--api-delete', action='store_true', help='delete indicator by name')
        parser_apiw.add_argument('--api-set', nargs='+', metavar="option=value",
                                 help='set generic indicator attributes (name=value), such as policy, description, '
                                      'checkmethod, silent, disabled, problem, retest, maintenance')


        parser_apio = parser.add_argument_group('API commands (obsolete. will be removed after 2021)')
        parser_apio.add_argument('--api-getarg', metavar='argument', default=None, help='OBSOLETE. Use --api-get')
        parser_apio.add_argument('--api-setarg', nargs='+', metavar="argname=value",
                                 help='OBSOLETE. Use --api-set')


        parser_apiw = parser.add_argument_group('Partner API commands')
        parser_apiw.add_argument('--partner-create', metavar=('partner_id', 'email'), nargs=2, help='create user')
        parser_apiw.add_argument('--partner-check', metavar='partner_id', help='check user info')
        parser_apiw.add_argument('--partner-list', default=False, action='store_true', help='list all users')
        parser_apiw.add_argument('--partner-grant', metavar=('partner_id', 'group'), nargs=2, help='grant user group')
        parser_apiw.add_argument('--partner-grant-new', metavar=('partner_id', 'group'), nargs=2, help='grant user new group')
        parser_apiw.add_argument('--partner-revoke', metavar=('partner_id', 'group', 'expiration'), nargs=3, help='revoke user from group')


        parser_apio = parser.add_argument_group('API options')
        parser_apio.add_argument('--api-url',  help='specify API URL (optional)',
                                 default=os.environ.get('OKERR_API_URL', None))
        parser_apio.add_argument('--api-user', help='okerr username', default=os.environ.get('OKERR_API_USER', None))
        parser_apio.add_argument('--api-pass', help='okerr password', default=os.environ.get('OKERR_API_PASS', None))
        parser_apio.add_argument('--api-key', help='API key', default=os.environ.get('OKERR_API_KEY', None))


    #
    # raises exception, so never returns
    def request_error(self, r):
        msg = '{}: {}'.format(r.status_code, r.text)
        self.log.error(msg)
        if r.status_code != 401:
            raise OkerrAuth(msg)
        raise OkerrExc(msg)


    def director(self, name=None):
        if name is None:
            name = self.textid

        url = urljoin(self.base_url, '/api/director/{}'.format(name))
        self.log.debug('getting project url from {}'.format(url))
        r = requests.get(url)
        self.log.debug('status code: {}'.format(r.status_code))
        if r.status_code != 200 or len(r.text)==0:
            self.log.error("No project found with textid {!r} on {}".format(name, self.base_url))
            raise ValueError("Invalid textid")
        return r.text.strip()

    def set_api_url(self,name=None):

        if self.api_url:
            self.log.debug("set_api_url already have url: {}".format(self.api_url))
            return

        self.api_url = self.director(name)



    def openlog(args,name='APILogger'):
        log = logging.getLogger(name)

        err = logging.StreamHandler(sys.stderr)
        log.addHandler(err)

        #log.setLevel(logging.INFO)

        return log

    def verbose(self):
        self.log.setLevel(logging.DEBUG)

    # main functions
    def indicators(self, prefix=''):

        self.set_api_url()

        url = urljoin(self.api_url, u'/api/indicators/{}/{}'.format(self.textid, prefix))
        self.log.debug('getting indicators list from url {}'.format(url))
        r = requests.get(url, auth=self.http_auth, headers=self.headers)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)
                       
        ilist = filter(None, r.text.strip().split('\n'))
        return ilist

    def indicator(self, iname):

        self.set_api_url()

        url = urljoin(self.api_url, u'/api/indicator/{}/{}'.format(self.textid, iname))
        self.log.debug(u'getting indicator from url {}'.format(url))
        r = requests.get(url, auth=self.http_auth, headers=self.headers)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)
        
        i = json.loads(r.text.strip().encode('utf-8'))
        return(i)
        # print r.text.strip().encode('utf-8')


    def partner_create(self, partner_id, email):
        data = {
            'email': email,
            'partner_id': partner_id,
        }

        # self.set_api_url(email)

        url = urljoin(self.base_url, u'/api/partner/create')
        self.log.debug(u'create user. email {} partner_id: {}'.format(email, partner_id))
        r = requests.post(url, auth=self.http_auth, data=data)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)

        print(r.text.strip().encode('utf-8'))

    def partner_check(self, partner_id):

        self.set_api_url('p:{}'.format(partner_id))

        url = urljoin(self.api_url, '/api/partner/check/{}'.format(partner_id))
        self.log.debug('check user. partner_id: {}'.format(partner_id))
        r = requests.get(url, auth=self.http_auth)
        self.log.debug('status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)

        print(r.text.strip().encode('utf-8'))

    def partner_grant(self, partner_id, group, new=False):

        self.set_api_url(u'p:{}'.format(partner_id))

        data = {
            'group': group,
            'partner_id': partner_id,
            'new': 0
        }

        if new:
            data['new']=1

        url = urljoin(self.api_url, u'/api/partner/grant')
        self.log.debug(u'grant group {} to user partner_id: {} url: {}'.format(group, partner_id, url))
        r = requests.post(url, auth=self.http_auth, data=data)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r.text)

        print(r.text.strip().encode('utf-8'))

    def partner_revoke(self, partner_id, group, expiration):

        data = {
            'group': group,
            'partner_id': partner_id,
            'exp': expiration
        }

        self.set_api_url('p:{}'.format(partner_id))

        url = urljoin(self.api_url, u'/api/partner/revoke')
        self.log.debug(u'revoke group {} (exp: {}) from partner_id: {}'.format(group, expiration, partner_id))
        r = requests.post(url, auth=self.http_auth, data=data)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r.text)

        print(r.text.strip().encode('utf-8'))




    def partner_list(self):

        url = urljoin(self.base_url, u'/api/partner/list')
        self.log.debug(u'partner/list users, url: {}'.format(url))
        r = requests.get(url, auth=self.http_auth)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)

        print(r.text.strip().encode('utf-8'))



    def create(self, iname):

        self.set_api_url()

        url = urljoin(self.api_url, u'/api/create/{}/{}'.format(self.textid, iname))
        self.log.debug(u'create indicator. url {}'.format(url))
        r = requests.post(url, auth=self.http_auth, headers=self.headers)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)

        print(r.text.strip())


    def delete(self, iname):

        self.set_api_url()

        url = urljoin(self.api_url, u'/api/delete/{}/{}'.format(self.textid, iname))
        self.log.debug(u'delete indicator. url {}'.format(url))
        r = requests.post(url, auth=self.http_auth, headers=self.headers)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)

        print(r.text.strip())

    def setarg(self, iname, args):

        data=dict()
        for arg in args:
            (k,v) = arg.split('=')
            data[k]=v

        self.set_api_url()

        url = urljoin(self.api_url, u'/api/setarg/{}/{}'.format(self.textid, iname))
        self.log.debug(u'set args for indicator. url {}'.format(url))
        r = requests.post(url, auth=self.http_auth, data=data, headers=self.headers)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)

        print(r.text.strip())


    def set(self, iname, args):

        data=dict()
        for arg in args:
            (k,v) = arg.split('=')
            data[k]=v

        self.set_api_url()

        url = urljoin(self.api_url, u'/api/set/{}/{}'.format(self.textid, iname))
        self.log.debug(u'set options for indicator. url {}'.format(url))
        r = requests.post(url, auth=self.http_auth, data=data, headers=self.headers)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)

        print(r.text.strip())


    def getarg(self, iname, argname):

        self.set_api_url()

        url = urljoin(self.api_url, u'/api/get/{}/{}/{}'.format(self.textid, iname,argname))
        self.log.debug('getting argument from url {}'.format(url))
        r = requests.get(url, auth=self.http_auth, headers=self.headers)
        self.log.debug('status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)
            return

        print(r.text.strip())


    def checkmethods(self):

        self.set_api_url()

        url = urljoin(self.api_url, '/api/checkmethods')
        self.log.debug('getting checkmethods from url {}'.format(url))
        r = requests.get(url) # NOAUTH
        self.log.debug('status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)
            return

        print(r.text.strip())


    def fltr(self, fltr):
        self.set_api_url()

        url = urljoin(self.api_url, '/api/filter/{}/'.format(self.textid))

        for f in fltr:
            url = urljoin(url, f+'/')

        self.log.debug('getting filtered indicators from url {}'.format(url))
        r = requests.get(url, auth=self.http_auth, headers=self.headers)
        self.log.debug(u'status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)            
            
        # print r.text.strip().encode('utf-8')
        ilist = filter(None, r.text.strip().split('\n'))
        return ilist


    def tagfilter(self, tags, notags):

        taglist = list()

        if tags:
            for tag in tags:
                taglist.append(tag)

        if notags:
            for tag in notags:
                taglist.append('-'+tag)

        self.log.debug("taglist: {}".format(taglist))

        self.set_api_url()

        url = urljoin(self.api_url, '/api/tagfilter/{}/'.format(self.textid))
        self.log.debug('url: {}'.format(url))

        for tag in taglist:
            url = urljoin(url, unicode(tag)+'/')

        self.log.debug('getting tag filter from url {}'.format(url))
        r = requests.get(url, auth=self.http_auth, headers=self.headers)
        self.log.debug('status code: {}'.format(r.status_code))
        if r.status_code != 200:
            self.request_error(r)

        print(r.text.strip())


    # handler

    def run_api_commands(self, args):

        worked = False

        # take options from CLI
        if args.defname:
            self.iname = args.defname
        if args.url:
            self.base_url = args.url
        if args.textid:
            self.textid = args.textid
        if args.api_user:
            self.api_user = args.api_user
        if args.api_pass:
            self.api_pass = args.api_pass
        if args.api_url:
            self.api_url = args.api_url
        if args.api_key:
            self.api_key = args.api_key

        if self.api_user and self.api_pass:
            self.http_auth = (self.api_user, self.api_pass)
        else:
            self.http_auth = None

        # build headers
        if self.api_key:
            self.headers['X-API-KEY'] = self.api_key

        if args.verbose:
            self.verbose()

        if args.partner_create:
            self.partner_create(args.partner_create[0], args.partner_create[1])
            worked = True

        if args.partner_check:
            self.partner_check(args.partner_check)
            worked = True

        if args.partner_list:
            self.partner_list()
            worked = True

        if args.partner_grant:
            self.partner_grant(args.partner_grant[0], args.partner_grant[1])
            worked = True

        if args.partner_grant_new:
            self.partner_grant(args.partner_grant_new[0], args.partner_grant_new[1], new=True)
            worked = True

        if args.partner_revoke:
            self.partner_revoke(args.partner_revoke[0], args.partner_revoke[1], args.partner_revoke[2])
            worked = True

        if args.api_create:
            self.create(self.iname)
            worked = True

        if args.api_director is not None:
            if args.api_director:
                name = args.api_director
            else:
                # not specified, use textid
                name = self.textid
            print(self.director(name))
            worked = True

        if args.api_indicator:
            i = self.indicator(self.iname)
            print(json.dumps(i, indent=4, sort_keys=True))
            worked = True

        if args.api_indicators is not None:
            ilist = self.indicators(args.api_indicators)
            for i in ilist:
                print(i)
            worked = True

        if args.api_fltr:
            ilist = self.fltr(args.api_fltr)
            for i in ilist:
                print(i)
            worked = True

        #if args.api_tags or args.api_notags:
        #    self.tagfilter(args.api_tags, args.api_notags)
        #    worked = True


        if args.api_get:
            self.getarg(self.iname, args.api_get)
            worked = True

        if args.api_getarg:
            # Compatibility code
            self.getarg(self.iname, args.api_getarg)
            worked = True


        if args.api_checkmethods:
            self.checkmethods()
            worked = True


        if args.api_set:
            self.set(self.iname, args.api_set)
            worked = True

        if args.api_setarg:
            # Compatibility code
            self.set(self.iname, args.api_setarg)
            worked = True

        if args.api_delete:
            self.delete(self.iname)
            worked = True

        return worked
