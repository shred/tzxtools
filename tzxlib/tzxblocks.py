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
import os

from tzxlib.tapfile import TapFile
from tzxlib.saver import TapeSaver

class TzxbBlock():
    blockTypes = {
        0x10: lambda: TzxbData(),
        0x11: lambda: TzxbTurboData(),
        0x12: lambda: TzxbPureTone(),
        0x13: lambda: TzxbPulseSequence(),
        0x14: lambda: TzxbPureData(),
        0x15: lambda: TzxbDirectRecording(),
        0x16: lambda: TzxbC64Data(),
        0x17: lambda: TzxbC64TurboData(),
        0x18: lambda: TzxbCswRecording(),
        0x19: lambda: TzxbGeneralizedData(),
        0x20: lambda: TzxbPause(),
        0x21: lambda: TzxbGroupStart(),
        0x22: lambda: TzxbGroupEnd(),
        0x23: lambda: TzxbJumpTo(),
        0x24: lambda: TzxbLoopStart(),
        0x25: lambda: TzxbLoopEnd(),
        0x26: lambda: TzxbCallSequence(),
        0x27: lambda: TzxbReturn(),
        0x28: lambda: TzxbSelect(),
        0x2A: lambda: TzxbStopTape48k(),
        0x2B: lambda: TzxbSetSignalLevel(),
        0x30: lambda: TzxbTextDescription(),
        0x31: lambda: TzxbMessage(),
        0x32: lambda: TzxbArchiveInfo(),
        0x33: lambda: TzxbHardwareType(),
        0x34: lambda: TzxbEmulationInfo(),
        0x35: lambda: TzxbCustomInfo(),
        0x40: lambda: TzxbSnapshot(),
        0x4B: lambda: TzxbKansasCityStandard(),
        0x5A: lambda: TzxbGlue(),
    }

    def createBlock(type):
        if not type in TzxbBlock.blockTypes:
            raise IOError('Unknown block type %02x' % (type))
        clazz = TzxbBlock.blockTypes[type]
        return clazz()

    def __init__(self):
        self.data = bytearray()

    def read(self, tzx):
        self.data = tzx.read(0x04)
        len = unpack('<L', self.data)[0]
        self.data += tzx.read(len)

    def write(self, tzx):
        tzx.write(bytes([self.id]))
        tzx.write(self.data)

    def writeTap(self, out):
        raise TapNotSupportedError

    def dump(self):
        return None

    def info(self):
        return None

    def playback(self, saver:TapeSaver):
        yield from ()

    def __str__(self):
        return ''


class TzxbData(TzxbBlock):
    id = 0x10
    type = 'Standard Speed Data Block'

    def setup(self, tap):
        self.tap = tap
        self.data = pack('<HH', 1000, len(tap.data))

    def read(self, tzx):
        self.data = tzx.read(0x04)
        len = unpack('<H', self.data[0x02:0x04])[0]
        self.tap = TapFile.create(tzx.read(len))

    def write(self, tzx):
        TzxbBlock.write(self, tzx)
        self.tap.write(tzx)

    def writeTap(self, out):
        self.tap.writeFragment(out)
        return True

    def valid(self):
        return self.tap.valid()

    def dump(self):
        return self.tap.body()

    def playback(self, saver:TapeSaver):
        yield from saver.saveTapFile(self.tap)
        yield from saver.pause(unpack('<H', self.data[0x00:0x02])[0])

    def __str__(self):
        return str(self.tap)


class TzxbTurboData(TzxbBlock):
    id = 0x11
    type = 'Turbo Speed Data Block'

    def read(self, tzx):
        self.data = tzx.read(0x12)
        len = unpack('<BBB', self.data[0x0F:0x12])
        len = len[2] << 16 | len[1] << 8 | len[0]
        self.tap = TapFile.create(tzx.read(len))

    def write(self, tzx):
        TzxbBlock.write(self, tzx)
        self.tap.write(tzx)

    def writeTap(self, out):
        self.tap.writeFragment(out)
        return True

    def valid(self):
        return self.tap.valid()

    def asData(self):
        (pilot, sync1, sync2, zerobit, onebit, tone, bits) = unpack('<HHHHHHB', self.data[0x00:0x0D])
        if (self.data[0x11] == 0
                and 2148 <= pilot   <= 2188
                and  657 <= sync1   <=  677
                and  725 <= sync2   <=  745
                and  845 <= zerobit <=  865
                and 1700 <= onebit  <= 1720
                and tone > 2000
                and bits == 8):
            # Standard size and standard timing, convert to Standard Speed Data Block
            result = TzxbData()
            result.data = self.data[0x0D:0x11]
            result.tap = self.tap
            return result
        return self

    def dump(self):
        return self.tap.body()

    def playback(self, saver:TapeSaver):
        (pilot, sync1, sync2, zerobit, onebit, tone, bits) = unpack('<HHHHHHB', self.data[0x00:0x0D])
        yield from saver.saveTapFile(self.tap,
            pilotPulse=pilot, syncHiPulse=sync1, syncLoPulse=sync2,
            zeroPulse=zerobit, onePulse=onebit, leaderTone=tone, finalBits=bits)
        yield from saver.pause(unpack('<H', self.data[0x0D:0x0F])[0])

    def __str__(self):
        return str(self.tap)


class TzxbPureTone(TzxbBlock):
    id = 0x12
    type = 'Pure Tone'

    def read(self, tzx):
        self.data = tzx.read(0x04)

    def info(self):
        return '%d x %d T-states' % unpack('<HH', self.data)

    def playback(self, saver:TapeSaver):
        (length, number) = unpack('<HH', self.data[0x00:0x04])
        yield from saver.tone(length, number)


class TzxbPulseSequence(TzxbBlock):
    id = 0x13
    type = 'Pulse Sequence'

    def read(self, tzx):
        self.data = tzx.read(0x01)
        len = unpack('<B', self.data)[0]
        self.data += tzx.read(len * 2)

    def info(self):
        return '{} pulses'.format((len(self.data)-1) // 2)

    def playback(self, saver:TapeSaver):
        for i in range(1, len(self.data), 2):
            length = unpack('<H', self.data[i:i+2])[0]
            yield from saver.pulse(length)


class TzxbPureData(TzxbBlock):
    id = 0x14
    type = 'Pure Data Block'

    def read(self, tzx):
        self.data = tzx.read(0x0A)
        len = unpack('<BBB', self.data[0x07:0x0A])
        len = len[2] << 16 | len[1] << 8 | len[0]
        self.tap = TapFile.create(tzx.read(len))

    def write(self, tzx):
        TzxbBlock.write(self, tzx)
        self.tap.write(tzx)

    def writeTap(self, out):
        self.tap.writeFragment(out)
        return True

    def valid(self):
        return self.tap.valid()

    def dump(self):
        return self.tap.body()

    def playback(self, saver:TapeSaver):
        (zerobit, onebit, bits, pause) = unpack('<HHBH', self.data[0x00:0x07])
        yield from saver.saveTapFile(self.tap,
            pilotPulse=None, syncHiPulse=None, syncLoPulse=None,
            zeroPulse=zerobit, onePulse=onebit, finalBits=bits)
        yield from saver.pause(pause)

    def __str__(self):
        return str(self.tap)


class TzxbDirectRecording(TzxbBlock):
    id = 0x15
    type = 'Direct Recording'

    def read(self, tzx):
        self.data = tzx.read(0x08)
        len = unpack('<BBB', self.data[0x05:0x08])
        len = len[2] << 16 | len[1] << 8 | len[0]
        self.data += tzx.read(len)

    def playback(self, saver:TapeSaver):
        (tstates, pause, bits) = unpack('<HHB', self.data[0x00:0x05])
        yield from saver.saveDirect(self.data[0x08:], bits, tstates)
        yield from saver.pause(pause)


class TzxbC64Data(TzxbBlock): # deprecated
    id = 0x16
    type = 'C64 ROM type data'

    def read(self, tzx):
        self.data = tzx.read(0x04)
        len = unpack('<L', self.data)[0]
        self.data += tzx.read(len - 4)

    def dump(self):
        return self.data[0x28:]

    def playback(self, saver:TapeSaver):
        raise NotImplementedError('C64 blocks are not supported')


class TzxbC64TurboData(TzxbBlock): # deprecated
    id = 0x17
    type = 'C64 turbo tape data'

    def read(self, tzx):
        self.data = tzx.read(0x04)
        len = unpack('<L', self.data)[0]
        self.data += tzx.read(len - 4)

    def dump(self):
        return self.data[0x16:]

    def playback(self, saver:TapeSaver):
        raise NotImplementedError('C64 blocks are not supported')


class TzxbCswRecording(TzxbBlock):
    id = 0x18
    type = 'CSW recording'

    def playback(self, saver:TapeSaver):
        raise NotImplementedError('CSW Recording Block is not supported yet')


class TzxbGeneralizedData(TzxbBlock):
    id = 0x19
    type = 'Generalized data'

    def playback(self, saver:TapeSaver):
        raise NotImplementedError('Generalized Data Block is not supported yet')


class TzxbPause(TzxbBlock):
    id = 0x20
    type = 'Pause'

    def read(self, tzx):
        self.data = tzx.read(0x02)

    def length(self):
        return unpack('<H', self.data)[0]

    def stopTheTape(self):
        return self.length() == 0

    def info(self):
        return '%d ms' % (self.length())

    def playback(self, saver:TapeSaver):
        yield from saver.pause(self.length())


class TzxbGroupStart(TzxbBlock):
    id = 0x21
    type = 'Group start'

    def read(self, tzx):
        self.data = tzx.read(0x01)
        len = unpack('<B', self.data)[0]
        self.data += tzx.read(len)

    def __str__(self):
        return self.data[1:].decode('ISO-8859-15').strip()


class TzxbGroupEnd(TzxbBlock):
    id = 0x22
    type = 'Group end'

    def read(self, tzx):
        pass


class TzxbJumpTo(TzxbBlock):
    id = 0x23
    type = 'Jump to'

    def read(self, tzx):
        self.data = tzx.read(0x02)

    def relative(self):
        return unpack('<h', self.data)[0]

    def __str__(self):
        return str(self.relative())


class TzxbLoopStart(TzxbBlock):
    id = 0x24
    type = 'Loop start'

    def read(self, tzx):
        self.data = tzx.read(0x02)

    def repeats(self):
        return unpack('<h', self.data)[0]

    def __str__(self):
        return str(self.repeats())


class TzxbLoopEnd(TzxbBlock):
    id = 0x25
    type = 'Loop end'

    def read(self, tzx):
        pass


class TzxbCallSequence(TzxbBlock):
    id = 0x26
    type = 'Call sequence'

    def read(self, tzx):
        self.data = tzx.read(0x02)
        len = unpack('<H', self.data)[0]
        self.data += tzx.read(len * 2)


class TzxbReturn(TzxbBlock):
    id = 0x27
    type = 'Return from sequence'

    def read(self, tzx):
        pass


class TzxbSelect(TzxbBlock):
    id = 0x28
    type = 'Select'

    def read(self, tzx):
        self.data = tzx.read(0x02)
        len = unpack('<H', self.data)[0]
        self.data += tzx.read(len)


class TzxbStopTape48k(TzxbBlock):
    id = 0x2A
    type = 'Stop the tape (48k)'

    def writeTap(self, out):
        return False


class TzxbSetSignalLevel(TzxbBlock):
    id = 0x2B
    type = 'Set signal level'

    def __str__(self):
        return "high" if self.data[0x04] == 1 else "low"


class TzxbTextDescription(TzxbBlock):
    id = 0x30
    type = 'Text description'

    def read(self, tzx):
        self.data = tzx.read(0x01)
        len = unpack('<B', self.data)[0]
        self.data += tzx.read(len)

    def writeTap(self, out):
        return False

    def dump(self):
        return self.data[1:]

    def info(self):
        return self.data[1:].decode('ISO-8859-15')


class TzxbMessage(TzxbBlock):
    id = 0x31
    type = 'Message'

    def read(self, tzx):
        self.data = tzx.read(0x02)
        len = unpack('<xB', self.data)[0]
        self.data += tzx.read(len)

    def writeTap(self, out):
        return False

    def dump(self):
        return self.data[2:]

    def info(self):
        return self.data[2:].decode('ISO-8859-15')


class TzxbArchiveInfo(TzxbBlock):
    id = 0x32
    type = 'Archive info'
    identifications = [
        'Title', 'Publisher', 'Author', 'Publication',
        'Language', 'Type', 'Price', 'Loader', 'Origin'
    ]

    def read(self, tzx):
        self.data = tzx.read(0x02)
        len = unpack('<H', self.data)[0]
        self.data += tzx.read(len)

    def writeTap(self, out):
        return False

    def info(self):
        result = ''
        ix = 0x03
        for _ in range(self.data[2]):
            (tp, tl) = unpack('BB', self.data[ix:ix+2])
            result += self.identifications[tp] if 0 <= tp < len(self.identifications) else 'Comment'
            result += ': '
            result += self.data[ix+2:ix+2+tl].decode('ISO-8859-15').replace('\r', '\n').replace('\n', '\n\t').strip()
            result += os.linesep
            ix += 2 + tl
        return result


class TzxbHardwareType(TzxbBlock):
    id = 0x33
    type = 'Hardware type'

    def read(self, tzx):
        self.data = tzx.read(0x01)
        len = unpack('<B', self.data)[0]
        self.data += tzx.read(len * 3)

    def writeTap(self, out):
        return False


class TzxbEmulationInfo(TzxbBlock): # deprecated
    id = 0x34
    type = 'Emulation info'

    def read(self, tzx):
        self.data = tzx.read(0x08)


class TzxbCustomInfo(TzxbBlock):
    id = 0x35
    type = 'Custom info'

    def read(self, tzx):
        self.data = tzx.read(0x14)
        len = unpack('<L', self.data[0x10:0x14])[0]
        self.data += tzx.read(len)

    def writeTap(self, out):
        return False

    def dump(self):
        return self.data[0x14:]

    def identification(self):
        return self.data[0:0x10].decode('ISO-8859-15')

    def info(self):
        txt = self.data[0x14:].decode('ISO-8859-15')
        return txt if '\0' not in txt else None

    def __str__(self):
        return self.identification().strip()


class TzxbSnapshot(TzxbBlock): # deprecated
    id = 0x40
    type = 'Snapshot'

    def read(self, tzx):
        self.data = tzx.read(0x04)
        len = unpack('<BBB', self.data[0x01:0x04])
        len = len[2] << 16 | len[1] << 8 | len[0]
        self.data += tzx.read(len)


class TzxbKansasCityStandard(TzxbBlock):
    id = 0x4B
    type = 'Kansas City Standard'

    def dump(self):
        return self.data[0x10:]

    def info(self):
        return "Data stream: {} bytes".format(len(self.data)-0x10)

    def playback(self, saver:TapeSaver):
        raise NotImplementedError('Kansas City Standard is not supported')


class TzxbGlue(TzxbBlock):
    id = 0x5A
    type = 'Glue'

    def read(self, tzx):
        tzx.read(0x09)

    def write(self, tzx):
        pass    # never write the glue block, it serves no purpose

    def writeTap(self, out):
        return False


class TapNotSupportedError(Exception):
    pass
