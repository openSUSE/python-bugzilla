#!/usr/bin/python
# Simple self-test of the bugzilla module

# Copyright (C) 2007 Red Hat Inc.
# Author: Will Woods <wwoods@redhat.com>
# 
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import sys
sys.path.insert(0, "..") # top dir
from bugzilla import Bugzilla
import os, glob
import xmlrpclib

# TODO: Rewrite with unittest! This is pretty bogus!

column_list = ['bug_id', 'bug_status', 'assigned_to', 'short_desc']
bugzillas = {
        'Red Hat Bugzilla':{
            'url':'https://bugzilla.redhat.com/xmlrpc.cgi',
            'public_bug':427301,
            'private_bug':250666,
            'bugidlist':(1,2,3,1337),
            'query':{'product':'Fedora',
                     'component':'python-bugzilla',
                     'version':'rawhide',
                     'column_list':column_list}
            },
        'Bugzilla 3.4':{
            'url':'https://landfill.bugzilla.org/bugzilla-3.4-branch/xmlrpc.cgi',
            'public_bug':4433,
            'private_bug':6620, # FIXME - does this instance have groups?
            'bugidlist':(1,2,3,4433),
            'query':{'product':'FoodReplicator',
                     'component':'SpiceDispenser',
                     'version':'1.0',
                     'status':'NEW'}
            },
        }

# TODO: add other instances? e.g.:
# 'https://landfill.bugzilla.org/bugzilla-3.2-branch/xmlrpc.cgi' - BZ3.2

def encoded_filename_test():
    '''A test for the fix for bug #663674'''
    attachid = 502352
    attachname = 'Karel Kl\xc3\xad\xc4\x8d memorial test file.txt' # in utf8
    bz = Bugzilla(url='https://bugzilla.redhat.com/xmlrpc.cgi')
    att = bz.openattachment(attachid)
    assert att.name.encode("utf8") == attachname

def selftest(data,user='',password=''):
    print "Using bugzilla at " + data['url']
    bz = Bugzilla(url=data['url'])
    print "Bugzilla class: %s" % bz.__class__
    if not bz.logged_in:
        if user and password:
            bz.login(user,password)
    if bz.logged_in:
        print "Logged in to bugzilla OK."
    else:
        print "Not logged in - create a .bugzillarc or provide user/password"
        # FIXME: only run some tests if .logged_in

    print "Reading product list"
    prod = bz.getproducts()
    prodlist = [p['name'] for p in prod]
    print "Products found: %s, %s, %s...(%i more)" % \
        (prodlist[0],prodlist[1],prodlist[2],len(prodlist)-3)

    p = data['query']['product']
    assert p in prodlist
    print "Getting component list for %s" % p
    comp = bz.getcomponents(p)
    print "%i components found" % len(comp)


    print "Reading public bug (#%i)" % data['public_bug']
    print bz.getbugsimple(data['public_bug'])
    print

    print "Reading private bug (#%i)" % data['private_bug']
    try:
        print bz.getbugsimple(data['private_bug'])
    except xmlrpclib.Fault, e:
        if 'NotPermitted' in e.faultString:
            print "Failed: Not authorized."
        else:
            print "Failed: Unknown XMLRPC error: %s"  % e
    except Exception, e:
        print "Failed: %s" % e
    print

    print "Reading multiple bugs, one-at-a-time: %s" % str(data['bugidlist'])
    for b in data['bugidlist']:
        print bz.getbug(b)
    print

    print "Reading multiple bugs, all-at-once: %s" % str(data['bugidlist'])
    for b in bz.getbugs(data['bugidlist']):
        print b
    print

    print "Querying: %s" % str(data['query'])
    try:
        bugs = bz.query(data['query'])
        print "%s bugs found." % len(bugs)
        bugs = bz.getbugs([bug.bug_id for bug in bugs]) # refresh bug data
        for bug in bugs:
            print "Bug %s" % bug
    except NotImplementedError:
        print "This bugzilla class doesn't support query()."
    print

if __name__ == '__main__':
    user = ''
    password = ''
    if len(sys.argv) > 2:
        (user,password) = sys.argv[1:3]

    print "Woo, welcome to the bugzilla.py self-test."
    for name,data in bugzillas.items():
        print "Testing %s" % name
        try:
            selftest(data,user,password)
        except KeyboardInterrupt:
            print "Exiting on keyboard interrupt."
            sys.exit(1)
    encoded_filename_test()
    print "Awesome. We're done."
