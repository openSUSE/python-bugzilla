# nvlbugzilla.py - a Python interface to Novell Bugzilla using xmlrpclib.
#
# Copyright (C) 2009 Novell Inc.
# Author: Michal Vyskocil <mvyskocil@suse.cz>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

#from bugzilla.base import BugzillaError, log
import bugzilla.base
from bugzilla import Bugzilla34

import urllib
import urllib2
import urlparse
import cookielib
import time
import re
import os

class NovellBugzilla(Bugzilla34):
    '''bugzilla.novell.com is a standard bugzilla 3.4 with some extensions.
    By default, it uses a proprietary IChain login system, but by using a special
    domain, you can force it to use HTTP Basic Auth instead.

    This class can also read credentials from ~/.oscrc if exists, so it does not have to
    be duplicated in /etc/bugzillarc or ~/.bugzillarc.
    '''
    
    version = '0.2'
    user_agent = bugzilla.base.user_agent + ' NovellBugzilla/%s' % version

    obs_url = 'https://api.opensuse.org/'

    def __init__(self, **kwargs):
        super(NovellBugzilla, self).__init__(**kwargs)

    def _login(self, user, password):
        # set up data for basic auth transport
        self._transport.auth_params = (self.user, self.password)

    def _logout(self):
        # using basic auth, no logout
        pass

    def connect(self, url):
        origurl = url
        spliturl = urlparse.urlsplit(url)
        # a piece of user-friendliness:
        # field "hostname" indicates that the supplied url was valid
        hostname = spliturl.hostname or url
        path = spliturl.hostname and spliturl.path or 'xmlrpc.cgi'
        # we have two bugzilla instances, both of which, with "api" prefix, accept basic auth login
        if not hostname.startswith('api'):
            hostname = 'api'+hostname

        # force https scheme (because of the basic auth)
        url = urlparse.urlunsplit(('https', hostname, path, spliturl.query, spliturl.fragment))
        return super(NovellBugzilla, self).connect(url)

    @classmethod
    def _read_osc_password(cls, c):
        # supports obfuscated passwords introduced in osc-0.121
        if c.has_option(cls.obs_url, 'passx'):
            return c.get(cls.obs_url, 'passx').decode('base64').decode('bz2')
        return c.get(cls.obs_url, 'pass')

    def readconfig(self, configpath=None):
        super(NovellBugzilla, self).readconfig(configpath)

        oscrc=os.path.expanduser('~/.oscrc')
        if not self.user or not self.password \
            and os.path.exists(oscrc):
            from ConfigParser import SafeConfigParser, NoOptionError
            c = SafeConfigParser()
            r = c.read(oscrc)
            if not r:
                return

            obs_url = self.__class__.obs_url
            if not c.has_section(obs_url):
                return

            try:
                user = c.get(obs_url, 'user')
                if self.user and self.user != user:
                    return
                else:
                    self.user = user
                self.password = self._read_osc_password(c)
                bugzilla.base.log.info("Read credentials from ~/.oscrc")
            except NoOptionError, ne:
                return


