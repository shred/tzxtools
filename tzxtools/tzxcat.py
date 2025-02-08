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
from tzxlib.tapfile import TapHeader
from tzxlib.convert import convertToText
from tzxlib.convert import convertToBasic
from tzxlib.convert import convertToDump
from tzxlib.convert import convertToAssembler
from tzxlib.convert import convertToScreen

def writeBlock(out, dump, converter, skip, length, org):
    if skip:
        if 0 <= skip < len(dump):
            dump = dump[skip:]
        else:
            dump = []
    if length:
        if 0 <= length < len(dump):
            dump = dump[:length]
    if converter:
        dump = converter(dump, out, org)
    return dump

def writeSingleBlock(tzx, out, index, writer, skipNotDumpable=False):
    if index < 0 or index >= len(tzx.blocks):
        print('Error: Block %d out of range' % (index), file=sys.stderr)
        exit(1)
    b = tzx.blocks[index]
    d = b.dump()
    if d is None:
        if skipNotDumpable:
            return
        else:
            print('Error: Block %d has no data content' % (index), file=sys.stderr)
            exit(1)
    if hasattr(b, 'tap') and not b.tap.valid():
        print('Warning: Block %d has bad CRC' % (index), file=sys.stderr)
    writer(out, d, findOrg(tzx, index))

def writeAllBlocks(tzx, out, writer):
    for i in range(len(tzx.blocks)):
        writeSingleBlock(tzx, out, i, writer, True)

def findOrg(tzx, index):
    if index > 1:
        b = tzx.blocks[index - 1]
        if hasattr(b, 'tap'):
            if isinstance(b.tap, TapHeader) and b.tap.typeId() == 3:
                return b.tap.param1()
    return None

def main():
    parser = argparse.ArgumentParser(description='Write data block content')
    parser.add_argument('file',
                nargs='?',
                type=argparse.FileType('rb'),
                default=(None if sys.stdin.isatty() else sys.stdin.buffer),
                help='TZX file, stdin if omitted')
    parser.add_argument('-b', '--block',
                dest='block',
                type=int,
                metavar='NR',
                help='block number to cat')
    parser.add_argument('-o', '--to',
                dest='to',
                metavar='TARGET',
                type=argparse.FileType('wb'),
                default=sys.stdout.buffer,
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
                help='convert ZX Spectrum text to plain text')
    parser.add_argument('-B', '--basic',
                dest='basic',
                action='store_true',
                help='convert ZX Spectrum BASIC to plain text')
    parser.add_argument('-A', '--assembler',
                dest='assembler',
                action='store_true',
                help='disassemble Z80 code')
    parser.add_argument('-S', '--screen',
                dest='screen',
                action='store_true',
                help='convert a ZX Spectrum SCREEN$ to PNG')
    parser.add_argument('-d', '--dump',
                dest='dump',
                action='store_true',
                help='convert to a hex dump')
    parser.add_argument('-O', '--org',
                dest='org',
                type=int,
                metavar='BASE',
                help='base address for disassembled code')
    args = parser.parse_args()

    if args.file is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    file = TzxFile()
    file.read(args.file)

    converter = lambda data, out, org: out.write(data)  # default binary output
    if args.basic:
        converter = convertToBasic
    elif args.assembler:
        converter = convertToAssembler
    elif args.screen:
        converter = convertToScreen
    elif args.text:
        converter = convertToText
    elif args.dump:
        converter = convertToDump

    writer = lambda out, dump, org : writeBlock(out, dump, converter, args.skip, args.length, args.org or org or 0)

    outf = args.to if args.to != '-' else sys.stdout.buffer
    with outf if isinstance(outf, io.IOBase) else open(outf, 'wb') as out:
        if args.block != None:
            writeSingleBlock(file, out, args.block, writer)
        else:
            writeAllBlocks(file, out, writer)
