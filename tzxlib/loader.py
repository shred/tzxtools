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

def unpackStereo(data, size, leftMix = 0.5):
    val = unpack('<' + size + size, data)
    return (val[0] * leftMix + val[1] * (1 - leftMix))

class TapeLoader():

    # Actual ZX Spectrum pulse timings:
    #  length of a half wave, in number of T-states
    leaderT = 2168      # leader pulse
    syncT   =  701      # sync pulse (on: 667, off: 735)
    lowT    =  855      # 0 bit pulse
    highT   = 1710      # 1 bit pulse

    def __init__(self, progress=None, debug=None, verbose=False, treshold=3500, tolerance=1.2, leaderMin=20, cpufreq=3500000, leftChMix=0.5):
        maxlenT = self.leaderT * 2.2 * tolerance
        self.samples = TapeReader(progress=progress, cpufreq=cpufreq, maxlenT=maxlenT, leftChMix=leftChMix)
        self.debug = debug if debug is not None else 0
        self.verbose = verbose
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
                    (tzxData, startPos, endPos) = self._loadBlock()
                    tzxbd.setup(tzxData)
                    tzx.blocks.append(tzxbd)
                    if self.verbose:
                        startMillis = self.samples.toMilliSeconds(startPos)
                        startSecs = startMillis // 1000
                        startMins = startSecs // 60
                        print(('{:3d}:{:02d}.{:03d} {:9d} - {:9d}: {}').format(
                             startMins,
                             startSecs % 60,
                             startMillis % 1000,
                             startPos,
                             endPos,
                             str(tzxbd)
                        ), file=sys.stderr)
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
                expectedSyncT = 1.1 * (sum(leaderLengths) * self.syncT) / (len(leaderLengths) * self.leaderT)
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
        letMeGuess = False

        while True:
            lowLen = self._testBitPulse(expectedLowT, '0')
            highLen = self._testBitPulse(expectedHighT, '1')

            # We detected a bit for sure?
            if lowLen is not None and lowLen[0]:
                letMeGuess = True
                self._advance(False, lowLen[1])
                tapCreator.shift(False)
                continue

            if highLen is not None and highLen[0]:
                letMeGuess = True
                self._advance(True, highLen[1])
                tapCreator.shift(True)
                continue

            # We're not sure, but maybe we're lucky...
            if lowLen is not None and highLen is None:
                self._advance(False, lowLen[1], tag='gap')
                tapCreator.shift(False)
                continue

            if highLen is not None and lowLen is None:
                self._advance(True, highLen[1], tag='gap')
                tapCreator.shift(True)
                continue

            # Hope for a broken Low bit, but not too often...
            if lowLen is not None and highLen is not None and letMeGuess:
                letMeGuess = False
                self._advance(False, lowLen[1], tag='noise')
                tapCreator.shift(False)
                continue

            # Seems we have lost the bit stream...
            if len(tapCreator) <= 2:
                raise BadBlock
            tap = tapCreator.createTap()
            if self.debug >= 1:
                self._showBlock(tap, leaderPos, syncPos, self.samples.position())
            return (tap, leaderPos, self.samples.position())

    def _testLeaderPulse(self):
        self.samples.ensure()
        self.lastPulse = self.samples.position()

        # Convert range to samples
        minRange = self.samples.toFrames(self.leaderT / ( 1.3 * self.tolerance))
        maxRange = self.samples.toFrames(self.leaderT * ( 1.1 * self.tolerance))

        # Find end of half pulse
        startSign = sgn(self.samples[0])
        count = 1
        while sgn(self.samples[count]) == startSign:
            count += 1
            if count > maxRange:
                return None

        if not (minRange <= count <= maxRange):
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
        frames = self.samples.toFrames(tCycles * 2)
        (minv, maxv, bias) = self.samples.minMaxAvg(frames)

        # Is amplitude above treshold?
        if abs(maxv - minv) < self.treshold:
            if self.debug >= 4:
                print(' ! - below treshold, {} < {}'.format(
                        abs(maxv - minv),
                        self.treshold), file=sys.stderr)
            return None

        # Find next zero crossing, normal signal
        self.samples.invert = False
        tag = '-'
        count = self._findZeroCrossing(frames, bias, tag)
        if not count:
            # Find next zero crossing, inverted signal
            self.samples.invert = True
            (minv, maxv, bias) = (-maxv, -minv, -bias)
            tag = '~'
            count = self._findZeroCrossing(frames, bias, tag)
            if not count:
                return None

        # Integrate both half waves
        countHalf = count // 2
        w1 = sum([self.samples[i] for i in range(0, countHalf)]) / countHalf
        w2 = sum([self.samples[i] for i in range(countHalf, count)]) / countHalf

        # Is it a full wave?
        if not (w1 < bias and w2 > bias and abs(w2 - w1) >= self.treshold / 2):
            if self.debug >= 4:
                print(' ! {} not a full wave, w1={} w2={} bias={}'.format(tag, w1, w2, bias), file=sys.stderr)
            return None

        # Success, this is a sync
        length = self.samples.toTStates(count / 2)
        if self.debug >= 3:
            print('   {} {:5d} @{:n}~{:n}'.format(tag, length, self.lastPulse, self.lastPulse + count), file=sys.stderr)
        self.samples.advance(count)
        return length

    def _testBitPulse(self, tCycles, tag):
        self.lastPulse = self.samples.position()
        self.samples.ensure()

        # Convert to samples
        frames = self.samples.toFrames(tCycles * 2)
        (minv, maxv, bias) = self.samples.minMaxAvg(frames)

        # Is amplitude above treshold?
        if abs(maxv - minv) < self.treshold:
            if self.debug >= 4:
                print(' ! {} below treshold, {} < {}'.format(
                        tag,
                        abs(maxv - minv),
                        self.treshold), file=sys.stderr)
            return None

        # Find next zero crossing
        count = self._findZeroCrossing(frames, bias, tag)
        if not count:
            return None

        # Integrate both half waves
        countHalf = count // 2
        w1 = sum([self.samples[i] for i in range(0, countHalf)]) / countHalf
        w2 = sum([self.samples[i] for i in range(countHalf, count)]) / countHalf

        # Is it a full wave?
        if not (w1 < bias and w2 > bias and abs(w2 - w1) >= self.treshold):
            if self.debug >= 4:
                print(' ! {} not a full wave, w1={} w2={} bias={}'.format(tag, w1, w2, bias), file=sys.stderr)
            return (False, count)

        # Success, this is a bit
        return (True, count)

    def _advance(self, bit, count, tag=''):
        self.samples.advance(count)
        if self.debug >= 3:
            length = self.samples.toTStates(count / 2)
            print('   {} {:5d} @{:n}~{:n} {}'.format(1 if bit else 0, length, self.lastPulse, self.lastPulse + count, tag), file=sys.stderr)

    def _findZeroCrossing(self, frames, bias, tag):
        count = frames
        countL = int(frames / self.tolerance)
        countH = int(frames * self.tolerance)

        while self.samples[count] <= bias:
            count -= 1
            if count < countL:
                if self.debug >= 4:
                    print(' ! {} no zero crossing detected, count={}, bias={}'.format(tag, count, bias), file=sys.stderr)
                return None

        while self.samples[count] > bias:
            count += 1
            if count > countH:
                if self.debug >= 4:
                    print(' ! {} no wave end in range, count={}, bias={}'.format(tag, count, bias), file=sys.stderr)
                return None

        return count

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
    def __init__(self, progress=None, cpufreq=3500000, maxlenT=6000, leftChMix=0.5):
        self.cpufreq = cpufreq
        self.progress = progress
        self.maxlenT = maxlenT
        self.invert = False
        self.startFrame = None
        self.endFrame = None
        self.leftChMix = leftChMix

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
                sf = skip if skip < 1000 else 1000
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

    def toMilliSeconds(self, frames):
        """ Converts number of frames to seconds """
        return int(frames * 1000 / self.wav.getframerate())

    def toFrames(self, tCycles):
        """ Converts T-States to number of frames """
        return int(tCycles * self.wav.getframerate() / self.cpufreq)

    def _createReader(self):
        """ Returns a function that converts frame byte array to sample data """
        channels = self.wav.getnchannels()
        bpc = self.wav.getsampwidth()
        if bpc == 2:
            if channels == 2:   return lambda f: unpackStereo(f, 'h', self.leftChMix)
            elif channels == 1: return lambda f: unpackMono(f, 'h')
            else:               raise IOError('Cannot handle WAV files with {} channels'.format(channels))
        elif bpc == 1:
            if channels == 2:   return lambda f: unpackStereo(f, 'b', self.leftChMix) * 256
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
