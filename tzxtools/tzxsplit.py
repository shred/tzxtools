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
import os.path
import re
import sys

from tzxlib.tapfile import TapHeader
from tzxlib.tzxfile import TzxFile

unwanted = re.compile(r'[^a-zA-Z0-9 #$%,;=@_{}()+-]')

def sanitize(name):
    if len(name) == 0:
        return 'no-name'
    return unwanted.sub('_', name)

def writeTzx(tzx, name, dir):
    if tzx is None or len(tzx.blocks) == 0: return # do not write empty TZX files
    count = 1
    while True:
        fn = '%s%s-%03d.tzx' % (dir, sanitize(name), count)
        if not os.path.isfile(fn): break
        count += 1
    tzx.write(fn)

def main():
    parser = argparse.ArgumentParser(description='Split into separate programs')
    parser.add_argument('file',
                nargs='?',
                type=argparse.FileType('rb'),
                default=(None if sys.stdin.isatty() else sys.stdin.buffer),
                help='TZX file, stdin if omitted')
    parser.add_argument('-d', '--dir',
                dest='dir',
                metavar='TARGET',
                default='./',
                help='target directory, default is cwd')
    parser.add_argument('-1', '--single',
                dest='single',
                action='store_true',
                help='split into single loadable files')
    parser.add_argument('-s', '--skip',
                dest='skip',
                action='store_true',
                help='skip all blocks before first Program')
    args = parser.parse_args()

    if args.file is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    file = TzxFile()
    file.read(args.file)

    dir = args.dir
    if dir[-1] != '/': dir += '/'

    fname = 'preamble'
    fout = TzxFile() if not args.skip else None

    for b in file.blocks:
        if hasattr(b, 'tap') and isinstance(b.tap, TapHeader) and (b.tap.typeId() == 0 or args.single):
            writeTzx(fout, fname, dir)
            fout = TzxFile()
            fname = b.tap.name().strip()
        if not fout is None:
            fout.blocks.append(b)

    writeTzx(fout, fname, dir)
