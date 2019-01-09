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
import sys

from tzxlib.tzxfile import TzxFile
from tzxlib.convert import convertToText
from tzxlib.convert import convertToBasic

def writeBlock(out, block, convert, basic, skip, length):
    data = block.tap.body()
    if skip:
        data = data[skip:]
    if length:
        data = data[:length]

    if basic:
        out.write(convertToBasic(data).encode('utf-8'))
    elif convert:
        out.write(convertToText(data).encode('utf-8'))
    else:
        out.write(data)

def writeSingleBlock(tzx, out, index, writer):
    if index < 0 or index >= len(tzx.blocks):
        print('Error: Block %d out of range' % (index), file=sys.stderr)
        exit(1)
    b = tzx.blocks[index]
    if not hasattr(b, 'tap'):
        print('Error: Block %d has no data content' % (index), file=sys.stderr)
        exit(1)
    if not b.tap.valid():
        print('Warning: Block %d has bad CRC' % (index), file=sys.stderr)
    writer(out, b)

def writeAllBlocks(tzx, out, writer):
    cnt = 0
    for b in tzx.blocks:
        if hasattr(b, 'tap'):
            if not b.tap.valid():
                print('Warning: Block %d has bad CRC' % (cnt), file=sys.stderr)
            writer(out, b)
        cnt += 1

def main():
    parser = argparse.ArgumentParser(description='Write data block content')
    parser.add_argument('file',
                nargs='?',
                default='/dev/stdin',
                help='TZX file, stdin if omitted')
    parser.add_argument('-b', '--block',
                dest='block',
                type=int,
                metavar='NR',
                help='block number to cat')
    parser.add_argument('-o', '--to',
                dest='to',
                metavar='TARGET',
                default='/dev/stdout',
                help='target file, stdout if omitted')
    parser.add_argument('-s', '--skip',
                dest='skip',
                type=int,
                metavar='BYTES',
                help='skip the given number of bytes before output')
    parser.add_argument('-l', '--length',
                dest='length',
                type=int,
                metavar='BYTES',
                help='limit output to the given number of bytes')
    parser.add_argument('-t', '--text',
                dest='text',
                action='store_true',
                help='convert ZX Spectrum text to UTF-8')
    parser.add_argument('-B', '--basic',
                dest='basic',
                action='store_true',
                help='convert ZX Spectrum BASIC to UTF-8 text')
    args = parser.parse_args()

    file = TzxFile()
    file.read(args.file or '/dev/stdin')

    writer = lambda out, block : writeBlock(out, block, args.text, args.basic, args.skip, args.length)

    with open(args.to, 'wb') as out:
        if args.block != None:
            writeSingleBlock(file, out, args.block, writer)
        else:
            writeAllBlocks(file, out, writer)
