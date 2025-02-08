#!/usr/bin/env python3
#
# tzxtools - a collection for processing tzx files
#
# Copyright (C) 2021 Richard "Shred" Körber
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
from math import sin, pi
import numpy
import sounddevice as sd
import struct
import sys
import time
import wave

from tzxlib.tapfile import TapHeader
from tzxlib.tzxfile import TzxFile
from tzxlib.tzxblocks import TzxbLoopStart, TzxbLoopEnd, TzxbJumpTo, TzxbPause, TzxbStopTape48k
from tzxlib.saver import TapeSaver


wavelets = {}
silence = bytes(2048)
numpySilence = numpy.zeros(1024, dtype=numpy.float32)


def wavelet(length, level, sine=False, npy=False):
    type = (length, level)
    if type in wavelets:
        return wavelets[type]

    sign = 1 if level else -1

    if npy:
        amp = sign * (min(32767 * (length + 10) / 25, 32767) if sine else 32000) / 32767
        wave = numpy.empty(length, dtype=numpy.float32)
        for pos in range(length):
            wave[pos] = amp * sin(pos * pi / length) if sine else amp
        wavelets[type] = wave

    else:
        amp = sign * (min(32767 * (length + 10) / 25, 32767) if sine else 32000)
        wave = bytearray(length*2)
        for pos in range(length):
            value = int(amp * sin(pos * pi / length) if sine else amp)
            wave[pos*2:pos*2+2] = struct.pack('<h', value)
            wavelets[type] = bytes(wave)
    return wavelets[type]


def streamAudio(tzx:TzxFile, rate=44100, stopAlways=False, stop48k=False, sine=False, cpufreq=3500000, verbose=False, npy=False):
    saver = TapeSaver(cpufreq)

    block = 0
    repeatBlock = None
    repeatCount = None
    currentSampleTime = 0
    realTimeNs = 0

    while block < len(tzx.blocks):
        b = tzx.blocks[block]
        if verbose:
            millis = realTimeNs // 1000000
            seconds = millis // 1000
            minutes = seconds // 60
            print('%02d:%02d.%03d %3d %-30s %s' % (minutes, seconds%60, millis%1000, block, b.type, str(b)))
        block += 1

        if isinstance(b, TzxbLoopStart):
            repeatBlock = block
            repeatCount = b.repeats()
            continue
        elif isinstance(b, TzxbLoopEnd) and repeatBlock is not None:
            repeatCount -= 1
            if repeatCount > 0:
                block = repeatBlock
                if verbose:
                    print('    - returning to block %d (remaining %d)' % (block, repeatCount))
            else:
                repeatBlock = None
                repeatCount = None
                if verbose:
                    print('    - loop is finished')
            continue
        elif isinstance(b, TzxbJumpTo):
            block += b.relative()-1
            if block < 0 or block > len(tzx.blocks)-1:
                raise IndexError('Jump to non-existing block')
            if verbose:
                print('    - jumping to block %d' % (block))
            continue
        elif isinstance(b, TzxbPause) and b.stopTheTape() and stopAlways:
            if verbose:
                print('    - tape stopped')
            break
        elif isinstance(b, TzxbStopTape48k) and stop48k:
            if verbose:
                print('    - tape stopped (48k mode)')
            break

        currentLevel = False
        lastLevel = False
        for ns in b.playback(saver):
            currentLevel = not currentLevel
            if ns > 0:
                realTimeNs += ns
                newSampleTime = ((realTimeNs * rate) + 500000000) // 1000000000
                wavelen = newSampleTime - currentSampleTime
                if wavelen <= 0:
                    continue
                if currentLevel != lastLevel:
                    yield wavelet(wavelen, currentLevel, sine, npy)
                else:
                    while wavelen > 0:
                        if wavelen >= len(silence)//2:
                            yield numpySilence if npy else silence
                            wavelen -= len(silence)//2
                        else:
                            yield numpy.zeros(wavelen, dtype=numpy.float32) if npy else silence[0:wavelen*2]
                            wavelen = 0
                lastLevel = currentLevel
                currentSampleTime = newSampleTime
    if verbose:
        millis = realTimeNs // 1000000
        seconds = millis // 1000
        minutes = seconds // 60
        print('%02d:%02d.%03d     End of Recording' % (minutes, seconds%60, millis%1000))


def main():
    parser = argparse.ArgumentParser(description='Playback a tzx file')
    parser.add_argument('file',
                nargs='?',
                type=argparse.FileType('rb'),
                default=(None if sys.stdin.isatty() else sys.stdin.buffer),
                help='TZX file, stdin if omitted')
    parser.add_argument('-o', '--to',
                dest='to',
                metavar='TARGET',
                type=argparse.FileType('wb'),
                default=None,
                help='Create WAV file instead of playing audio')
    parser.add_argument('-v', '--verbose',
                dest='verbose',
                action='store_true',
                help='Be verbose about what you are doing')
    parser.add_argument('-s', '--stop',
                dest='stop',
                action='store_true',
                help='Execute Stop-The-Tape commands')
    parser.add_argument('-K', '--48k',
                dest='mode48k',
                action='store_true',
                help='Enable ZX Spectrum 48K mode')
    parser.add_argument('-r', '--rate',
                dest='rate',
                default=44100,
                type=int,
                help='Output sample rate')
    parser.add_argument('-c', '--clock',
                dest='clock',
                default=3500000,
                type=int,
                help='Reference Z80 CPU clock, in Hz')
    parser.add_argument('-S', '--sine',
                dest='sine',
                action='store_true',
                help='Generate soft sine pulses (square pulses otherwise)')
    args = parser.parse_args()

    if args.file is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    tzx = TzxFile()
    tzx.read(args.file)
    stream = streamAudio(tzx, rate=args.rate, stopAlways=args.stop, stop48k=args.mode48k,
                        sine=args.sine, cpufreq=args.clock, verbose=args.verbose, npy=args.to is None)

    audiostream = audio = wav = None

    try:
        if args.to is not None:
            # Generate WAV file
            wav = wave.open(args.to, mode='wb')
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(args.rate)
            for b in stream:
                wav.writeframesraw(b)
            wav.writeframesraw(silence[0:16])
        else:
            # Audio Playback
            with sd.Stream(samplerate=args.rate, channels=1, latency='high') as out:
                for b in stream:
                    out.write(b)
    except KeyboardInterrupt:
        print('', file=sys.stderr)
        print("D BREAK - CONT repeats, 0:1", file=sys.stderr)
    finally:
        if wav is not None:
            wav.close()
        if audiostream is not None:
            audiostream.stop_stream()
            audiostream.close()
        if audio is not None:
            audio.terminate()
