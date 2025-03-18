# coding=utf-8
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

import os
from sys import getdefaultencoding
from struct import unpack
from tzxlib.z80dis import disassemble

UPPER = [ ' ', '▝', '▘', '▀', '▗', '▐', '▚', '▜', '▖', '▞', '▌', '▛', '▄', '▟',
    '▙', '█', 'Ⓐ', 'Ⓑ', 'Ⓒ', 'Ⓓ', 'Ⓔ', 'Ⓕ', 'Ⓖ', 'Ⓗ', 'Ⓘ', 'Ⓙ', 'Ⓚ',
    'Ⓛ', 'Ⓜ', 'Ⓝ', 'Ⓞ', 'Ⓟ', 'Ⓠ', 'Ⓡ', 'Ⓢ', 'Ⓣ', 'Ⓤ', 'RND', 'INKEY$',
    'PI', 'FN ', 'POINT ', 'SCREEN$ ', 'ATTR ', 'AT ', 'TAB ', 'VAL$ ',
    'CODE ', 'VAL ', 'LEN ', 'SIN ', 'COS ', 'TAN ', 'ASN ', 'ACS ', 'ATN ',
    'LN ', 'EXP ', 'INT ', 'SQR ', 'SGN ', 'ABS ', 'PEEK ', 'IN ', 'USR ',
    'STR$ ', 'CHR$ ', 'NOT ', 'BIN ', ' OR ', ' AND ', '<=', '>=', '<>',
    ' LINE ', ' THEN ', ' TO ', ' STEP ', ' DEF FN ', ' CAT ', ' FORMAT ',
    ' MOVE ', ' ERASE ', ' OPEN #', ' CLOSE #', ' MERGE ', ' VERIFY ',
    ' BEEP ', ' CIRCLE ', ' INK ', ' PAPER ', ' FLASH ', ' BRIGHT ',
    ' INVERSE ', ' OVER ', ' OUT ', ' LPRINT ', ' LLIST ', ' STOP ', ' READ ',
    ' DATA ', ' RESTORE ', ' NEW ', ' BORDER ', ' CONTINUE ', ' DIM ', ' REM ',
    ' FOR ', ' GO TO ', ' GO SUB ', ' INPUT ', ' LOAD ', ' LIST ', ' LET ',
    ' PAUSE ', ' NEXT ', ' POKE ', ' PRINT ', ' PLOT ', ' RUN ', ' SAVE ',
    ' RANDOMIZE ', ' IF ', ' CLS ', ' DRAW ', ' CLEAR ', ' RETURN ', ' COPY ' ]

def convChar(ch, noLeadingSpace=False):
    if ch == 0x0D:   return '\n'
    elif ch >= 0x80:
        result = UPPER[ch - 0x80]
        if noLeadingSpace and ch >= 0xA5 and result[0] == ' ':
            return result[1:]
        else:
            return result
    elif ch == 0x5E: return '↑'
    elif ch == 0x60: return '£'
    elif ch == 0x7F: return '©'
    else:            return chr(ch)

def convert(data):
    result = ''
    for d in data:
        if d >= 0x20:
            result += convChar(d, result[-1:] == ' ')
    return result

def convertCR(data):
    result = ''
    for d in data:
        if d >= 0x20 or d == 0x0D:
            result += convChar(d, result[-1:] == ' ')
    return result

def decodeBasicLine(line):
    result = ''
    pos = 0
    while pos < len(line):
        ch = line[pos]
        pos += 1
        if 0x10 <= ch <= 0x15:
            pos += 1
        elif 0x16 <= ch <= 0x17:
            pos += 2
        elif ch == 0x0E:
            pos += 5
        else:
            result += convChar(ch, result[-1:] == ' ')
    return result

def convertToText(data, out, org=0):
    out.write(convertCR(data).replace('\n', os.linesep).encode(getdefaultencoding()))

def convertToBasic(data, out, org=0):
    pos = 0
    end = len(data)
    while pos + 4 < end:
        lineNum = unpack('>H', data[pos + 0 : pos + 2])[0]
        lineLen = unpack('<H', data[pos + 2 : pos + 4])[0]
        if pos + lineLen + 4 > end:
            break
        line = '%4d%s' % (lineNum, decodeBasicLine(unpack('%dB' % (lineLen), data[pos + 4 : pos + 4 + lineLen])))
        out.write(line.replace('\n', os.linesep).encode(getdefaultencoding()))
        pos += lineLen + 4

def convertToDump(data, out, org=0, bytesPerRow=16):
    pos = 0
    end = len(data)
    while pos < end:
        line = '%04X | ' % (pos + org)
        text = ''
        for x in range(bytesPerRow):
            if pos + x < end:
                line += '%02X ' % (data[pos + x])
                ch = data[pos + x]
                if ch < 32:
                    text += '‧'
                else:
                    ch = convChar(ch)
                    if len(ch) == 1:
                        text += ch
                    else:
                        text += '‧'
            else:
                line += '   '
        line += '| '
        line += text
        line += '\n'
        out.write(line.replace('\n', os.linesep).encode(getdefaultencoding()))
        pos += bytesPerRow

def convertToAssembler(data, out, org=0):
    pos = 0
    end = len(data)
    while pos < end:
        try:
            (ins, length) = disassemble(data, pos, org)
        except:
            (ins, length) = ('???', 1)
        line = '%04X  ' % (pos + org)
        for x in range(6):
            if x == 5 and length > 6:
                line += '...'
            elif x < length:
                line += '%02X ' % (data[pos + x])
            else:
                line += '   '
        line += ' '
        line += ins
        line += '\n'
        out.write(line.replace('\n', os.linesep).encode(getdefaultencoding()))
        pos += length

def convertToScreen(data, out, org=0):
    pixel = []
    for y in range(192):
        pixrow = []
        pixel.append(pixrow)
        for col in range(32):
            palette = readColor(data, y, col)
            bits = readBits(data, y, col)
            for b in range(8):
                if bits & (0b10000000 >> b):
                    pixrow.append(palette[0])
                else:
                    pixrow.append(palette[1])

    import png
    pngw = png.Writer(256, 192, palette=PALETTE)
    pngw.write(out, pixel)

def readBits(data, y, col):
    block = int(y / 64)
    line = int((y % 64) / 8)
    row = y % 8
    offset = ((((block * 8) + row) * 8) + line) * 32 + col
    return data[offset] if offset < len(data) else 0

def readColor(data, y, col):
    row = (int)(y / 8)
    offset = 6144 + row * 32 + col
    cols = data[offset] if offset < len(data) else 0b00111000
    if cols & 0b01000000:
        return ((cols % 8 & 0x07), (cols >> 3 & 0x07 + 8))
    else:
        return ((cols & 0x07), (cols >> 3 & 0x07))

PALETTE = [
    (0,0,0), (0,0,215), (215,0,0), (215,0,215), (0,215,0), (0,215,215), (215,215,0), (215,215,215),
    (0,0,0), (0,0,255), (255,0,0), (255,0,255), (0,255,0), (0,255,255), (255,255,0), (255,255,255),
]
