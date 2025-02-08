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

def appendRange(ranges, v1, v2, lastBlock):
    if v1 < 0: v1 += lastBlock
    if v1 < 0: v1 = 0
    if v2 < 0: v2 += lastBlock
    if v2 < 0: v2 = 0
    ranges.append((v1, v2))

def isInRange(ranges, num):
    for rng in ranges:
        if num >= rng[0] and num <= rng[1]:
            return True
    return False

def main():
    parser = argparse.ArgumentParser(description='Split into separate programs')
    parser.add_argument('blocks',
                nargs='*',
                help='block numbers or ranges to keep (range limits are separated by colon)')
    parser.add_argument('-i', '--from',
                dest='file',
                metavar='SOURCE',
                type=argparse.FileType('rb'),
                default=(None if sys.stdin.isatty() else sys.stdin.buffer),
                help='source TZX file, stdin if omitted')
    parser.add_argument('-o', '--to',
                dest='to',
                metavar='TARGET',
                type=argparse.FileType('wb'),
                default=sys.stdout.buffer,
                help='target TZX file, stdout if omitted')
    parser.add_argument('-v', '--invert',
                dest='invert',
                action='store_true',
                help='do not keep, but remove the blocks')
    args = parser.parse_args()

    if args.file is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    file = TzxFile()
    file.read(args.file)
    lastBlock = len(file.blocks)

    ranges = []
    for rng in args.blocks:
        m = re.match(r'^(-?\d+)$', rng)
        if m:
            v1 = int(m.group(1))
            appendRange(ranges, v1, v1, lastBlock)
            continue
        m = re.match(r'^(-?\d+):(-?\d+)$', rng)
        if m:
            v1 = int(m.group(1))
            v2 = int(m.group(2))
            appendRange(ranges, v1, v2, lastBlock)
            continue
        m = re.match(r'^(-?\d+):$', rng)
        if m:
            v1 = int(m.group(1))
            appendRange(ranges, v1, lastBlock, lastBlock)
            continue
        m = re.match(r'^:(-?\d+)$', rng)
        if m:
            v2 = int(m.group(1))
            appendRange(ranges, 0, v2, lastBlock)
            continue
        print('Illegal range: %s' % (rng), file=sys.stderr)
        exit(1)

    fout = TzxFile()

    count = 0
    for b in file.blocks:
        if isInRange(ranges, count) != args.invert:
            fout.blocks.append(b)
        count += 1

    fout.write(args.to)
