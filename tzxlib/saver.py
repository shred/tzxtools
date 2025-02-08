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

from tzxlib.tapfile import TapFile

BYTE_ORDER = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]

class TapeSaver():
    def __init__(self, cpufreq=3500000):
        self.cpufreq = cpufreq
        self.currentState = False

    def pulse(self, length):
        self.currentState = not self.currentState
        yield self.tStatesToNs(length)

    def tone(self, length, number):
        lstates = self.tStatesToNs(length)
        for _ in range(number // 2):
            yield lstates
            yield lstates
        if number % 2 == 1:
            self.currentState = not self.currentState
            yield lstates

    def saveTapFile(self, tap, pilotPulse=2168, syncHiPulse=667, syncLoPulse=735,
                    zeroPulse=855, onePulse=1710, leaderTone=None, finalBits=8):
        # Generate leader tone
        if pilotPulse is not None:
            lpulse = self.tStatesToNs(pilotPulse)
            for _ in range(leaderTone if leaderTone is not None else tap.leaderCycles() // 2):
                yield lpulse
                yield lpulse

        # Generate sync pulse
        if syncHiPulse is not None:
            yield self.tStatesToNs(syncHiPulse)
        if syncLoPulse is not None:
            yield self.tStatesToNs(syncLoPulse)

        # Send all bits
        counter = finalBits
        lone = self.tStatesToNs(onePulse)
        lzero = self.tStatesToNs(zeroPulse)
        for i in range(len(tap.data)):
            b = tap.data[i]
            for m in BYTE_ORDER:
                if b & m != 0:
                    yield lone
                    yield lone
                else:
                    yield lzero
                    yield lzero
                if i == len(tap.data)-1:
                    counter -= 1
                    if counter <= 0:
                        break

    def saveDirect(self, data, finalBits, tstates):
        if len(data) == 0:
            return
        counter = finalBits
        lstate = self.tStatesToNs(tstates)
        for i in range(len(data)):
            b = data[i]
            for m in BYTE_ORDER:
                newState = b & m != 0
                if newState == self.currentState:
                    yield 0
                yield lstate
                self.currentState = newState
                if i == len(data)-1:
                    counter -= 1
                    if counter <= 0:
                        break

    def pause(self, milliseconds):
        if milliseconds > 0:
            if not self.currentState:
                yield 0
            self.currentState = False
            yield milliseconds * 1000000

    def tStatesToNs(self, tstates):
        return tstates * 1000000000 // self.cpufreq
