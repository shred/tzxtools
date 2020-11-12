#!/usr/bin/env python3
#
# tzxtools - a collection for processing tzx files
#
# Copyright (C) 2018 Richard "Shred" Körber
#   https://github.com/shred/tzxtools
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

from tzxlib.tzxfile import TzxFile

def writeBlock(block, out, ignore, index):
    if not hasattr(block, 'tap'):
        if ignore:
            print('Warning: Block %d has no data content, ignored' % (index), file=sys.stderr)
            return
        else:
            print('Error: Block %d has no data content' % (index), file=sys.stderr)
            exit(1)
    if not block.tap.valid():
        print('Warning: Block %d has bad CRC' % (index), file=sys.stderr)
    block.tap.writeFragment(out)

def writeAllBlocks(tzx, out, ignore):
    index = 0
    for block in tzx.blocks:
        writeBlock(block, out, ignore, index)
        index += 1

def main():
    parser = argparse.ArgumentParser(description='Convert to TAP file format')
    parser.add_argument('file',
                nargs='?',
                type=argparse.FileType('rb'),
                default=(None if sys.stdin.isatty() else sys.stdin.buffer),
                help='TZX file, stdin if omitted')
    parser.add_argument('-o', '--to',
                dest='to',
                metavar='TARGET',
                type=argparse.FileType('wb'),
                default=sys.stdout.buffer,
                help='TAP file, stdout if omitted')
    parser.add_argument('-i', '--ignore',
                dest='ignore',
                action='store_true',
                help='ignore blocks that cannot be stored in a TAP file')
    args = parser.parse_args()

    if args.file is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    file = TzxFile()
    file.read(args.file)

    outf = args.to if args.to != '-' else sys.stdout.buffer
    with outf if isinstance(outf, io.IOBase) else open(outf, 'wb') as tap:
        writeAllBlocks(file, tap, args.ignore)
