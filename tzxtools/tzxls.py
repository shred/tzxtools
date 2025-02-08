#!/usr/bin/env python3
#
# tzxtools - a collection for processing tzx files
#
# Copyright (C) 2016 Richard "Shred" Körber
#   https://codeberg.org/shred/tzxtools
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import argparse
import io
import sys
import textwrap

from tzxlib.tapfile import TapHeader
from tzxlib.tzxfile import TzxFile

def main():
    parser = argparse.ArgumentParser(description='List the contents of a TZX file')
    parser.add_argument('file',
                nargs=argparse.REMAINDER,
                type=argparse.FileType('rb'),
                help='TZX files, stdin if omitted')
    parser.add_argument('-s', '--short',
                dest='short',
                action='store_true',
                help='list only the ZX Spectrum header names')
    parser.add_argument('-v', '--verbose',
                dest='verbose',
                action='store_true',
                help='show content of information blocks')
    args = parser.parse_args()

    files = list(args.file)
    if not sys.stdin.isatty() and len(files) == 0:
        files.append(sys.stdin.buffer)

    if len(files) == 0:
        parser.print_help(sys.stderr)
        sys.exit(1)

    for f in files:
        if len(files) > 1:
            name = f.name if hasattr(f, 'name') else f
            print('\n%s:' % (name))
        tzx = TzxFile()
        tzx.read(f)

        cnt = 0
        for b in tzx.blocks:
            if args.short:
                if hasattr(b, 'tap') and isinstance(b.tap, TapHeader):
                    print('%s: %s' % (b.tap.type(), b.tap.name()))
            else:
                print('%3d  %-27s %s' % (cnt, b.type, str(b)))
            if args.verbose:
                info = b.info()
                if info is not None:
                    print(textwrap.indent(info.strip(), '\t'))
            cnt += 1
