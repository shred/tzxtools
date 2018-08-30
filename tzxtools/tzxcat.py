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

def writeBlock(out, block, index, convert, basic):
    if not block.tap.valid():
        print('Warning: Block %d has bad CRC' % (index), file=sys.stderr)
    if basic:
        out.write(convertToBasic(block.tap.body()).encode('utf-8'))
    elif convert:
        out.write(convertToText(block.tap.body()).encode('utf-8'))
    else:
        block.tap.writeBody(out)

def writeSingleBlock(tzx, out, index, convert, basic):
    if index < 0 or index >= len(tzx.blocks):
        print('Error: Block %d out of range' % (index), file=sys.stderr)
        exit(1)
    b = tzx.blocks[index]
    if not hasattr(b, 'tap'):
        print('Error: Block %d has no data content' % (index), file=sys.stderr)
        exit(1)
    writeBlock(out, b, index, convert, basic)

def writeAllBlocks(tzx, out, convert, basic):
    cnt = 0
    for b in tzx.blocks:
        if hasattr(b, 'tap'):
            writeBlock(out, b, cnt, convert, basic)
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

    with open(args.to, 'wb') as out:
        if args.block != None:
            writeSingleBlock(file, out, args.block, args.text, args.basic)
        else:
            writeAllBlocks(file, out, args.text, args.basic)
