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

import io
import sys

from tzxlib.tzxblocks import TzxbBlock

class TzxFile():
    MAJOR = 1
    MINOR = 20

    def __init__(self):
        self._reset()

    def _reset(self):
        self.version = (TzxFile.MAJOR, TzxFile.MINOR)
        self.blocks = list()

    def read(self, input):
        self._reset()
        inf = input
        if isinstance(inf, io.TextIOWrapper):
            inf = inf.buffer
        with inf if isinstance(inf, io.IOBase) else open(inf, 'rb') as tzx:
            self.version = self._readHeader(tzx)
            while True:
                blockType = tzx.read(1)
                if not blockType: break
                block = TzxbBlock.createBlock(blockType[0])
                block.read(tzx)
                self.blocks.append(block)

    def write(self, output):
        outf = output
        if isinstance(outf, io.TextIOWrapper):
            outf = outf.buffer
        with outf if isinstance(outf, io.IOBase) else open(outf, 'wb') as tzx:
            self._writeHeader(tzx)
            for b in self.blocks:
                b.write(tzx)

    def _readHeader(self, tzx):
        header = tzx.read(10)
        if header[0:7].decode('ascii') != 'ZXTape!' or header[7] != 0x1A:
            raise IOError('Not a TZX file')
        if header[8] != TzxFile.MAJOR:
            raise IOError('Cannot handle TZX with major version %d' % (header[8]))
        return (header[8], header[9])

    def _writeHeader(self, tzx):
        tzx.write('ZXTape!'.encode('ascii'))
        tzx.write(bytes([0x1A, TzxFile.MAJOR, TzxFile.MINOR]))
