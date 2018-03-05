# coding=utf-8
#
# tzxtools - a collection for processing tzx files
#
# Copyright (C) 2018 Richard "Shred" Körber
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

from struct import unpack

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

def convertToText(data):
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

def convertToBasic(data):
    result = ''
    pos = 0
    end = len(data)
    while pos + 4 < end:
        lineNum = unpack('>H', data[pos + 0 : pos + 2])[0]
        lineLen = unpack('<H', data[pos + 2 : pos + 4])[0]
        if pos + lineLen + 4 > end:
            break
        result += '%4d' % (lineNum)
        result += decodeBasicLine(unpack('%dB' % (lineLen), data[pos + 4 : pos + 4 + lineLen]))
        pos += lineLen + 4
    return result
