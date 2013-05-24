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

from bugzilla import Bugzilla34, log

import urlparse

class NovellBugzilla(Bugzilla34):
    '''
    bugzilla.novell.com is a standard bugzilla 3.4 with some extensions.
    By default, it uses a proprietary AccessManager login system, but by using a special
    domain, you can force it to use HTTP Basic Auth instead.

    This class can also read credentials from ~/.oscrc if exists, so it does not have to
    be duplicated in /etc/bugzillarc or ~/.bugzillarc.
    '''

    version = '0.3'

    OBS_URL = 'https://api.opensuse.org'

    def __init__(self, **kwargs):
        super(NovellBugzilla, self).__init__(**kwargs)

    def _login(self, user, password):
        # set up data for basic auth transport
        self._transport.auth_params = (self.user, self.password)
        return ''

    def _logout(self):
        # using basic auth, no logout
        pass

    def connect(self, url=None):
        if url is None:
            url = 'https://apibugzilla.novell.com/xmlrpc.cgi'
        else:
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

    def readconfig(self, configpath=None):
        super(NovellBugzilla, self).readconfig(configpath)

        if not self.user or not self.password:
            try:
                import osc.conf
                osc.conf.get_config()
                conf = osc.conf.config['api_host_options'][self.OBS_URL]
                user = conf.get('user')
                pasw = conf.get('pass')
                if self.user and self.user != user:
                    return
                self.user = user
                self.password = pasw
                log.info("Read credentials from ~/.oscrc")
            except:
                pass
