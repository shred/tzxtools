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

from struct import pack, unpack

from tzxlib.convert import convert

class TapFile():
    def create(data):
        if len(data) == 19 and data[0] == 0x00:
            return TapHeader(data)
        else:
            return TapData(data)

    def valid(self):
        val = 0;
        for b in self.data:
            val ^= b
        return val == 0

    def body(self):
        return self.data[1:-1]

    def leaderCycles(self):
        return 3223

    def writeBody(self, out):
        out.write(self.body())

    def write(self, tzx):
        tzx.write(self.data)

    def writeFragment(self, tzx):
        tzx.write(pack('<H', len(self.data)))
        tzx.write(self.data)


class TapHeader(TapFile):
    def __init__(self, data):
        self.data = data

    def type(self):
        typeId = self.typeId()
        if typeId == 0: return 'Program'
        elif typeId == 1: return 'Number array'
        elif typeId == 2: return 'Character array'
        elif typeId == 3: return 'Bytes'
        else: return 'Unknown (%d)' % (typeId)

    def typeId(self):
        return self.data[1]

    def name(self):
        if self.data[2] == 0xFF:
            return ''
        else:
            return convert(self.data[2:12])

    def param1(self):
        return unpack('<H', self.data[14:16])[0]

    def param2(self):
        return unpack('<H', self.data[16:18])[0]

    def length(self):
        return unpack('<H', self.data[12:14])[0]

    def leaderCycles(self):
        return 8063

    def __str__(self):
        if (self.data[1] == 3):
            if (self.param1() == 0x4000 and self.length() == 6912):
                result = 'Screen: %s' % (self.name())
            else:
                result = '%s: %s (start: %s, %s bytes)' % (self.type(), self.name(), self.param1(), self.length())
        else:
            result = '%s: %s (%s bytes)' % (self.type(), self.name(), self.length())
        if not self.valid():
            result += ', CRC ERROR!'
        return result


class TapData(TapFile):
    def __init__(self, data):
        self.data = data

    def length(self):
        return len(self.data) - 2

    def __str__(self):
        if len(self.data) < 2:
            result = '%d bytes of incomplete data' % (len(self.data))
        elif self.data[0] == 0x00:
            result = '%d bytes of bogus header' % (len(self.data) - 2)
        else:
            result = '%d bytes of data' % (len(self.data) - 2)
        if not self.valid():
            result += ', CRC ERROR!'
        return result
