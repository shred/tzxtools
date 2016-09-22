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

from collections import deque
from struct import unpack
import sys
import wave

from tzxlib.tapfile import TapFile, TapHeader, TapData
from tzxlib.tzxblocks import TzxbData
from tzxlib.tzxfile import TzxFile

def sgn(val):
    return 1 if val >= 0 else -1

def unpackMono(data, size):
    return unpack('<' + size, data)[0]

def unpackStereo(data, size):
    val = unpack('<' + size + size, data)
    return (val[0] + val[1]) / 2

class TapeLoader():

    # Actual ZX Spectrum pulse timings:
    #  length of a half wave, in number of T-states
    leaderT = 2168      # leader pulse
    syncT   =  701      # sync pulse (on: 667, off: 735)
    lowT    =  855      # 0 bit pulse
    highT   = 1710      # 1 bit pulse

    def __init__(self, progress=None, debug=None, treshold=3500, tolerance=1.3, leaderMin=20, cpufreq=3500000):
        maxlenT = self.leaderT * 2.2 * tolerance
        self.samples = TapeReader(progress=progress, cpufreq=cpufreq, maxlenT=maxlenT)
        self.debug = debug if debug is not None else 0
        self.treshold = treshold
        self.tolerance = tolerance
        self.leaderMin = leaderMin

    def load(self, filename, startFrame=None, endFrame=None):
        try:
            self.samples.open(filename)
            self.samples.fileRange(startFrame, endFrame)
            tzx = TzxFile()
            while True:
                try:
                    tzxbd = TzxbData()
                    tzxbd.setup(self._loadBlock())
                    tzx.blocks.append(tzxbd)
                except BadBlock:
                    continue    # Try again with the next block
                except EOFError:
                    break       # we're done!
        finally:
            self.samples.close()
        return tzx

    def _loadBlock(self):
        tapCreator = TapCreator()
        if self.debug >= 2:
            tapCreator.callback = lambda val, crc, lng: \
                    print('   > {:5d}: {:02x} {:c} CRC={:02x}'.format(
                            lng,
                            val,
                            val if 0x20 <= val < 0x80 else 0x20,
                            crc), file=sys.stderr)
        self.samples.invert = False

        # Wait for leader
        self.samples.nextRaisingEdge()
        length = self._testLeaderPulse()
        while length is None:
            self.samples.advance(self.samples.toFrames(self.leaderT / self.tolerance))
            self.samples.nextRaisingEdge()
            length = self._testLeaderPulse()
        leaderPos = self.lastPulse

        # Skip leader, wait for sync
        leaderLengths = deque([length], maxlen=max(self.leaderMin, 20))
        while True:
            length = self._testLeaderPulse()
            if length is not None:
                leaderLengths.append(length)
                continue

            if len(leaderLengths) >= self.leaderMin:
                expectedSyncT = (sum(leaderLengths) * self.syncT) / (len(leaderLengths) * self.leaderT)
                length = self._testSyncPulse(expectedSyncT)
                if length is not None:
                    # Sync was found
                    syncPos = self.lastPulse
                    break

            # Leader was lost
            raise BadBlock()

        # Read data block
        expectedLowT = (sum(leaderLengths) * self.lowT) / (len(leaderLengths) * self.leaderT)
        expectedHighT = (sum(leaderLengths) * self.highT) / (len(leaderLengths) * self.leaderT)

        while True:
            lowLen = self._testBitPulse(expectedLowT, '0')
            if lowLen is not None:
                tapCreator.shift(False)
                continue

            highLen = self._testBitPulse(expectedHighT, '1')
            if highLen is not None:
                tapCreator.shift(True)
                continue

            if len(tapCreator) <= 2:
                raise BadBlock
            tap = tapCreator.createTap()
            if self.debug >= 1:
                self._showBlock(tap, leaderPos, syncPos, self.samples.position())
            return tap

    def _testLeaderPulse(self):
        self.samples.ensure()
        self.lastPulse = self.samples.position()

        # Convert range to samples
        minRange = self.samples.toFrames(self.leaderT / self.tolerance)
        maxRange = self.samples.toFrames(self.leaderT * self.tolerance)

        # Find end of half pulse
        startSign = sgn(self.samples[0])
        count = 1
        while sgn(self.samples[count]) == startSign:
            count += 1
            if count > maxRange:
                return None

        if not (minRange <= count <= maxRange):
            return None

        # Middle of pulse must be between average and min/max
        mma = self.samples.minMaxAvg(count)
        if (startSign >= 0 and self.samples[count // 2] < mma[2]) or (startSign < 0 and self.samples[count // 2] > mma[2]):
            return None

        # Compute pulse duration in Z80 T-states
        length = self.samples.toTStates(count)
        if self.debug >= 3:
            print('   # {:5d} @{:n}~{:n}'.format(length, self.lastPulse, self.lastPulse + count), file=sys.stderr)
        self.samples.advance(count)
        return length

    def _testSyncPulse(self, tCycles):
        self.lastPulse = self.samples.position()
        self.samples.ensure()

        # Convert to samples
        frames = self.samples.toFrames(tCycles) * 2
        mma = self.samples.minMaxAvg(frames)

        # Is amplitude above treshold?
        if abs(mma[1] - mma[0]) < self.treshold:
            if self.debug >= 4:
                print(' ! - below treshold, {} < {}'.format(
                        abs(mma[1] - mma[0]),
                        self.treshold), file=sys.stderr)
            return None

        # Is it a full wave?
        if self.samples[frames // 4] > mma[2] and self.samples[frames * 3 // 4] < mma[2]:
            invert = False
            tag = '-'
        elif self.samples[frames // 4] < mma[2] and self.samples[frames * 3 // 4] > mma[2]:
            invert = True
            tag = '~'
        else:
            if self.debug >= 4:
                print(' ! - not a full wave, lo={} hi={} bias={}'.format(
                        self.samples[frames // 4],
                        self.samples[frames * 3 // 4],
                        mma[2]), file=sys.stderr)
            return None

        # Find next zero crossing
        count = frames * 3 // 4
        while (invert == False and self.samples[count] < mma[2]) or (invert == True and self.samples[count] > mma[2]):
            count += 1
            limit = int(frames * self.tolerance)
            if count >= limit:
                if self.debug >= 4:
                    print(' ! - no wave end in range, bias={} limit={}'.format(mma[2], limit), file=sys.stderr)
                return None

        # Success, this is a sync
        self.samples.invert = invert
        length = self.samples.toFrames(count / 2)
        if self.debug >= 3:
            print('   {} @{:n}~{:n} {} {} {}'.format(tag, self.lastPulse, self.lastPulse + count, mma[0], mma[1], mma[2]), file=sys.stderr)
        self.samples.advance(count)
        return length

    def _testBitPulse(self, tCycles, tag):
        self.lastPulse = self.samples.position()
        self.samples.ensure()

        # Convert to samples
        frames = self.samples.toFrames(tCycles) * 2
        mma = self.samples.minMaxAvg(frames)

        # Is amplitude above treshold?
        if abs(mma[1] - mma[0]) < self.treshold:
            if self.debug >= 4:
                print(' ! {} below treshold, {} < {}'.format(
                        tag,
                        abs(mma[1] - mma[0]),
                        self.treshold), file=sys.stderr)
            return None

        # Is it a full wave?
        if not (self.samples[frames // 4] > mma[2] and self.samples[frames * 3 // 4] < mma[2]):
            if self.debug >= 4:
                print(' ! {} not a full wave, lo={} hi={} bias={}'.format(
                        tag,
                        self.samples[frames // 4],
                        self.samples[frames * 3 // 4],
                        mma[2]), file=sys.stderr)
            return None

        # Find next zero crossing
        count = frames * 3 // 4
        while self.samples[count] < mma[2]:
            count += 1
            limit = int(frames * self.tolerance)
            if count >= limit:
                 # nothing found, assume a wave with average length
                if self.debug >= 4:
                    print(' ! {} no wave end in range, bias={} limit={}'.format(tag, mma[2], limit), file=sys.stderr)
                count = frames
                break

        # Success, this is a bit
        length = self.samples.toFrames(count / 2)
        if self.debug >= 3:
            print('   {} @{:n}~{:n}'.format(tag, self.lastPulse, self.lastPulse + count), file=sys.stderr)
        self.samples.advance(count)
        return length

    def _showBlock(self, tap, leaderPos, syncPos, endPos):
        if isinstance(tap, TapHeader):
            print('=== {}: {}'.format(tap.type(), tap.name()), file=sys.stderr)
            if tap.typeId() == 3:
                print(' Start: {}, Expected length: {}'.format(tap.param1(), tap.length()), file=sys.stderr)
            else:
                print(' Expected length: {}'.format(tap.length()), file=sys.stderr)
        else:
            print('--- data', file=sys.stderr)
            print(' Length: {}'.format(tap.length()), file=sys.stderr)

        if not tap.valid():
            print(' CRC ERROR!', file=sys.stderr)

        print(' Leader: @{:n}, Sync: @{:n}, End: @{:n}'.format(leaderPos, syncPos, endPos), file=sys.stderr)



class TapeReader():
    def __init__(self, progress=None, cpufreq=3500000, maxlenT=6000):
        self.cpufreq = cpufreq
        self.progress = progress
        self.maxlenT = maxlenT
        self.invert = False
        self.startFrame = None
        self.endFrame = None

    def open(self, filename):
        """ Opens the given WAV file name """
        self.wav = wave.open(filename, 'r')
        self.frameCount = 0
        self.readFrame = self._createReader()
        self.bytesPerFrame = self.wav.getnchannels() * self.wav.getsampwidth()
        self.maxlen = self.toFrames(self.maxlenT)
        self.samples = deque(maxlen=self.maxlen)

    def fileRange(self, startFrame, endFrame):
        self.startFrame = startFrame
        self.endFrame = endFrame

    def close(self):
        """ Closes the tape reader """
        if self.progress is not None:
            self.progress(self.wav.getnframes(), self.wav.getnframes())
        self.wav.close()

    def __len__(self):
        """ Current length of sample buffer """
        return len(self.samples)

    def __getitem__(self, ix):
        """ Gets the sample at given index """
        return self.samples[ix] if not self.invert else -self.samples[ix]

    def position(self):
        """ Returns current frame position """
        return self.frameCount

    def ensure(self, needed=None):
        """ Ensures buffer is filled with sufficient samples """
        if self.startFrame is not None and self.frameCount < self.startFrame:
            skip = self.startFrame - self.frameCount
            self.frameCount = self.startFrame
            self.startFrame = None
            while skip > 0:
                sf = skip % 1000
                skip -= sf
                frames = self.wav.readframes(sf)
                if not frames:
                    raise EOFError()

        if needed is not None and len(self.samples) >= needed:
            return # sufficient data available

        missing = self.samples.maxlen - len(self.samples)
        if missing <= 0:
            return # buffer is filled to maximum

        frames = self.wav.readframes(missing)
        if not frames:
            raise EOFError()

        for ix in range(0, len(frames), self.bytesPerFrame):
            self.samples.append(self.readFrame(frames[ix:ix+self.bytesPerFrame]))

    def advance(self, frames):
        """ Advance number of frames """
        if frames == 0:
            return
        self.ensure(frames)
        for i in range(0, frames):
            self.samples.popleft()
        self.frameCount += frames
        if self.endFrame is not None and self.frameCount > self.endFrame:
            raise EOFError()
        if self.progress is not None:
            self.progress(self.frameCount, self.wav.getnframes())

    def minMaxAvg(self, frames):
        """ Returns a tuple of minimum, maximum and average of given range """
        self.ensure(frames)
        data = [self[i] for i in range(0, frames)]
        return (min(data), max(data), sum(data) / frames)

    def nextRaisingEdge(self):
        """ Finds the next raising edge """
        self.ensure(2)
        while not (self[0] < 0 and self[1] >= 0):
            self.advance(1)
            self.ensure(2)
        self.advance(1) # position on the first positive value

    def toTStates(self, frames):
        """ Converts number of frames to T-States """
        return int(frames * self.cpufreq / self.wav.getframerate())

    def toFrames(self, tCycles):
        """ Converts T-States to number of frames """
        return int(tCycles * self.wav.getframerate() / self.cpufreq)

    def _createReader(self):
        """ Returns a function that converts frame byte array to sample data """
        channels = self.wav.getnchannels()
        bpc = self.wav.getsampwidth()
        if bpc == 2:
            if channels == 2:   return lambda f: unpackStereo(f, 'h')
            elif channels == 1: return lambda f: unpackMono(f, 'h')
            else:               raise IOError('Cannot handle WAV files with {} channels'.format(channels))
        elif bpc == 1:
            if channels == 2:   return lambda f: unpackStereo(f, 'b') * 256
            elif channels == 1: return lambda f: unpackMono(f, 'b') * 256
            else:               raise IOError('Cannot handle WAV files with {} channels'.format(channels))
        else:
            raise IOError('Cannot handle WAV files with {} bits per channel'.format(bpc * 8))



class TapCreator():
    def __init__(self, callback=None):
        self.data = bytearray()
        self.crc = 0
        self.shifter = 0
        self.bits = 0
        self.callback = callback

    def shift(self, bit):
        """ Shifts in a bit """
        self.shifter <<= 1
        if bit: self.shifter |= 1

        self.bits += 1
        if self.bits == 8:
            self.crc ^= self.shifter
            self.data.append(self.shifter)
            if self.callback is not None:
                self.callback(self.shifter, self.crc, len(self.data))
            self.shifter = 0
            self.bits = 0

    def __len__(self):
        """ Current length of collected data, in bytes """
        return len(self.data)

    def createTap(self):
        """ Creates a TapFile from the collected data """
        return TapFile.create(self.data)



class BadBlock(Exception):
    """ Cannot read this block, try the next one. """
    pass
