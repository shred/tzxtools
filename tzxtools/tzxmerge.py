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
import sys

from tzxlib.tzxfile import TzxFile

def main():
    parser = argparse.ArgumentParser(description='Merges TZX files')
    parser.add_argument('files',
                nargs='+',
                type=argparse.FileType('rb'),
                default=sys.stdin.buffer,
                help='TZX files to merge')
    parser.add_argument('-o', '--to',
                metavar='TARGET',
                type=argparse.FileType('wb'),
                default=sys.stdout.buffer,
                help='target TZX file, stdout if omitted')
    args = parser.parse_args()

    file = TzxFile()

    for f in args.files:
        mergeFile = TzxFile()
        mergeFile.read(f)
        file.blocks.extend(mergeFile.blocks)

    file.write(args.to)
