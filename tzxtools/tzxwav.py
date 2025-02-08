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
import io
import sys
from time import time
import wave

from tzxlib.loader import TapeLoader

tresholds  = { 'low': 500, 'med': 2500, 'high':5000 }
tolerances = { 'low': 1.1,  'med': 1.2,  'high': 1.4 }
leaderMins = { 'none': 2, 'short': 10, 'normal': 40, 'long': 100 }
leftChMix = { 'left': 1,  'mix': 0.5,  'right': 0 }

lastPercent = None
startTime = None

def showProgress(current, max):
    global lastPercent, startTime
    if startTime is None:
        startTime = time()
    percent = int(current * 100 / max)
    if lastPercent is None or percent != lastPercent:
        lastPercent = percent
        halfPercent = int(percent / 2)
        if lastPercent > 3:
            now = time()
            remainSecs = ((now - startTime) * 100 / lastPercent) + startTime - now
            print('%3d%% |%s%s| %2d:%02d' % (percent, '#'*halfPercent, '-'*(50-halfPercent), remainSecs // 60 , remainSecs % 60), end='\r', file=sys.stderr)
        else:
            print('%3d%% |%s%s|' % (percent, '#'*halfPercent, '-'*(50-halfPercent)), end='\r', file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='Generates TZX from WAV file')
    parser.add_argument('file',
                nargs='?',
                type=argparse.FileType('rb'),
                default=(None if sys.stdin.isatty() else sys.stdin.buffer),
                help='WAV file')
    parser.add_argument('-o', '--to',
                dest='to',
                metavar='TARGET',
                type=argparse.FileType('wb'),
                default=sys.stdout.buffer,
                help='target file, stdout if omitted')
    parser.add_argument('-p', '--progress',
                dest='progress',
                action='store_true',
                help='show progress bar')
    parser.add_argument('-v', '--verbose',
                dest='verbose',
                action='store_true',
                help='show blocks as they are found')
    parser.add_argument('-t', '--treshold',
                choices=['low', 'med', 'high'],
                default='med',
                dest='treshold',
                help='sound/noise ratio treshold')
    parser.add_argument('-T', '--tolerance',
                choices=['low', 'med', 'high'],
                default='med',
                dest='tolerance',
                help='tape speed flutter tolerance')
    parser.add_argument('-l', '--leader',
                choices=['none', 'short', 'normal', 'long'],
                default='normal',
                dest='leader',
                help='accepted minimal length of leader signal')
    parser.add_argument('-c', '--clock',
                dest='clock',
                default=3500000,
                type=int,
                help='Reference Z80 CPU clock, in Hz')
    parser.add_argument('-s', '--start',
                dest='start',
                type=int,
                help='Start at WAV frame number')
    parser.add_argument('-e', '--end',
                dest='end',
                type=int,
                help='End at WAV frame number')
    parser.add_argument('-S', '--stereo',
                choices=['left', 'mix', 'right'],
                default='mix',
                dest='leftChMix',
                help='channel selection (works only for stereo WAV files)')
    parser.add_argument('-D', '--debug',
                dest='debug',
                action='count',
                help='enable debug output, give multiple times to increase verbosity')

    args = parser.parse_args()

    if args.file is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    loader = TapeLoader(debug=args.debug,
            treshold=tresholds[args.treshold],
            tolerance=tolerances[args.tolerance],
            leaderMin=leaderMins[args.leader],
            leftChMix=leftChMix[args.leftChMix],
            cpufreq=args.clock,
            progress=showProgress if args.progress else None,
            verbose=args.verbose)

    try:
        tzx = loader.load(args.file, startFrame=args.start, endFrame=args.end)
        file = args.to
        if not isinstance(file, io.IOBase) and not file.lower().endswith('.tzx'):
            file += '.tzx'
        tzx.write(file)
    except KeyboardInterrupt:
        print('', file=sys.stderr)
        print("D BREAK - CONT repeats, 0:1", file=sys.stderr)
        exit(1)

    if args.progress:
        print('', file=sys.stderr)
