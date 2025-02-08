#!/usr/bin/env python3
#
# tzxtools - a collection for processing tzx files
#
# Copyright (C) 2018 Richard "Shred" Körber
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

from tzxlib.tzxfile import TzxFile
from tzxlib.tzxblocks import TapNotSupportedError

def writeBlock(block, out, ignore, index):
    try:
        if block.writeTap(out):
            if not block.tap.valid():
                print('Block %3d: Warning: Bad CRC, may cause tape loading error.' % (index), file=sys.stderr)
        else:
            print('Block %3d: Comment block was ignored.' % (index), file=sys.stderr)
    except TapNotSupportedError:
        if ignore:
            print('Block %3d: Warning: Block is not supported by TAP format.' % (index), file=sys.stderr)
        else:
            print('Block %3d: Error: Block is not supported by TAP format.' % (index), file=sys.stderr)
            print('Use --ignore option to enforce conversion, but TAP file will be faulty.', file=sys.stderr)
            exit(1)

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
