# python-bugzilla - a Python interface to bugzilla using xmlrpclib.
#
# Copyright (C) 2007, 2008 Red Hat Inc.
# Author: Will Woods <wwoods@redhat.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

__version__ = "0.7.0"
version = __version__

import logging
import xmlrpclib

log = logging.getLogger("bugzilla")


from bugzilla.bugzilla3 import Bugzilla3, Bugzilla32, Bugzilla34, Bugzilla36
from bugzilla.bugzilla4 import Bugzilla4
from bugzilla.nvlbugzilla import NovellBugzilla
from bugzilla.rhbugzilla import RHBugzilla, RHBugzilla3, RHBugzilla4

# advertised class list
classlist = ['Bugzilla3', 'Bugzilla32', 'Bugzilla34',
             'Bugzilla36', 'Bugzilla4', 'RHBugzilla3', 'RHBugzilla4',
             'NovellBugzilla']




def getBugzillaClassForURL(url):
    log.debug("Choosing subclass for %s" % url)
    s = xmlrpclib.ServerProxy(url)
    rhbz = False
    bzversion = ''
    c = None

    # Check for a Red Hat extension
    try:
        log.debug("Checking for Red Hat Bugzilla extension")
        extensions = s.Bugzilla.extensions()
        if extensions.get('extensions', {}).get('RedHat', False):
            rhbz = True
    except xmlrpclib.Fault:
        pass
    log.debug("rhbz=%s" % str(rhbz))

    # Try to get the bugzilla version string
    try:
        log.debug("Checking return value of Buzilla.version()")
        r = s.Bugzilla.version()
        bzversion = r['version']
    except xmlrpclib.Fault:
        pass
    log.debug("bzversion='%s'" % str(bzversion))

    # note preference order: RHBugzilla* wins if available
    if rhbz:
        c = RHBugzilla
    else:
        if bzversion.startswith("4."):
            c = Bugzilla4
        elif bzversion.startswith('3.6'):
            c = Bugzilla36
        elif bzversion.startswith('3.4'):
            c = Bugzilla34
        elif bzversion.startswith('3.2'):
            c = Bugzilla32
        else:
            log.debug("No explicit match for %s, fall through", bzversion)
            c = Bugzilla3

    return c


class Bugzilla(object):
    '''Magical Bugzilla class that figures out which Bugzilla implementation
    to use and uses that. Requires 'url' parameter so we can check available
    XMLRPC methods to determine the Bugzilla version.'''
    def __init__(self, **kwargs):
        log.info("Bugzilla v%s initializing" % __version__)
        if 'url' not in kwargs:
            raise TypeError("You must pass a valid bugzilla xmlrpc.cgi URL")

        # pylint: disable=W0233
        # Use of __init__ of non parent class

        c = getBugzillaClassForURL(kwargs['url'])
        if c:
            self.__class__ = c
            c.__init__(self, **kwargs)
            log.info("Chose subclass %s v%s" % (c.__name__, c.version))
        else:
            raise ValueError("Couldn't determine Bugzilla version for %s" %
                             kwargs['url'])
