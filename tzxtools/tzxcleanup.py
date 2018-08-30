#!/usr/bin/env python3
#
# tzxtools - a collection for processing tzx files
#
# Copyright (C) 2016 Richard "Shred" Körber
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
import sys

from tzxlib.tzxfile import TzxFile

def main():
    parser = argparse.ArgumentParser(description='Remove all noise, idealize the data')
    parser.add_argument('file',
                nargs='?',
                default='/dev/stdin',
                help='TZX file, stdin if omitted')
    parser.add_argument('-o',
                '--to',
                dest='to',
                metavar='TARGET',
                default='/dev/stdout',
                help='target TZX file, stdout if omitted')
    parser.add_argument('-c',
                '--stripcrc',
                dest='stripcrc',
                action='store_true',
                help='also remove blocks with bad CRC')
    args = parser.parse_args()

    fout = TzxFile()
    crcCnt = 0
    noiseCnt = 0

    file = TzxFile()
    file.read(args.file)
    for b in file.blocks:
        # Convert Turbo blocks to standard timed blocks if possible
        if b.id in [0x11, 0x14]:
            o = b.asData()

        # Use all data blocks for the output
        if b.id in [0x10, 0x11, 0x14]:
            if not b.valid():
                crcCnt += 1
            if b.valid() or not args.stripcrc:
                fout.blocks.append(b)
            continue

        # Use all pause blocks if they mean "stop the tape"
        if b.id in [0x20, 0x2A]:
            if b.id != 0x20 or b.length() == 0:
                fout.blocks.append(b)
            continue

        # Use all meta blocks
        if b.id not in [0x12, 0x13, 0x15, 0x18, 0x19]:
            fout.blocks.append(b)
            continue

        noiseCnt += 1

    fout.write(args.to)

    print('Blocks found:           %3d' % (len(file.blocks)), file=sys.stderr)
    print('Noise blocks removed:   %3d' % (noiseCnt), file=sys.stderr)
    print('Blocks with CRC errors: %3d' % (crcCnt), file=sys.stderr)
    print('Blocks written:         %3d' % (len(fout.blocks)), file=sys.stderr)
