#! /usr/bin/env python

# This file is part of IVRE.
# Copyright 2011 - 2019 Pierre LALET <pierre.lalet@cea.fr>
#
# IVRE is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IVRE is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IVRE. If not, see <http://www.gnu.org/licenses/>.

"""Create views from nmap and passive databases."""

from __future__ import print_function
import sys

from ivre.db import db, DB
from ivre.view import from_passive, from_nmap, to_view

try:
    import argparse
    USING_ARGPARSE = True
except ImportError:
    import optparse
    USING_ARGPARSE = False


def main():
    if USING_ARGPARSE:
        parser = argparse.ArgumentParser(description=__doc__,
                                         parents=[DB().argparser])
    else:
        parser = optparse.OptionParser(description=__doc__)
        parser.parse_args_orig = parser.parse_args

        def my_parse_args():
            res = parser.parse_args_orig()
            res[0].ensure_value('ips', res[1])
            return res[0]
        parser.parse_args = my_parse_args
        parser.add_argument = parser.add_option

    fltnmap = db.nmap.flt_empty
    fltpass = db.passive.flt_empty
    _from = []

    parser.add_argument('--view-category', metavar='CATEGORY',
                        help='Choose a different category than the default')
    parser.add_argument('--test', '-t', action='store_true',
                        help='Give results in standard output instead of '
                             'inserting them in database.')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='For test output, print out formatted results.')

    if not USING_ARGPARSE:
        if 'nmap' in sys.argv:
            for args, kargs in db.nmap.argparser.args:
                parser.add_option(*args, **kargs)
        elif 'passive' in sys.argv:
            for args, kargs in db.passive.argparser.args:
                parser.add_option(*args, **kargs)
        else:
            print('ivre db2view: error: invalid subcommand {nmap, passive}.')
            sys.exit(-1)
    else:
        subparsers = parser.add_subparsers(dest='view_source',
                                           help="Accepted values are 'nmap' "
                                                "and 'passive'. None or 'all' "
                                                "will do both")

        subparsers.add_parser('nmap', parents=[db.nmap.argparser])
        subparsers.add_parser('passive', parents=[db.passive.argparser])
        subparsers.add_parser('all')

    args = parser.parse_args()

    view_category = args.view_category
    if not args.view_source:
        args.view_source = 'all'
    if args.view_source == 'all':
        fltnmap = DB().parse_args(args, flt=fltnmap)
        fltpass = DB().parse_args(args, flt=fltpass)
        _from = [from_nmap(fltnmap, category=view_category),
                 from_passive(fltpass, category=view_category)]
    elif args.view_source == 'nmap':
        fltnmap = db.nmap.parse_args(args, fltnmap)
        _from = [from_nmap(fltnmap, category=view_category)]
    elif args.view_source == 'passive':
        fltpass = db.passive.parse_args(args, fltpass)
        _from = [from_passive(fltpass, category=view_category)]
    if args.test:

        def output(x):
            print(x)
    else:
        output = db.view.store_or_merge_host
    # Output results
    itr = to_view(_from)
    if not itr:
        return
    for elt in itr:
        output(elt)
