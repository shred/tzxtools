# coding=utf-8
#
# tzxtools - a collection for processing tzx files
#
# Copyright (C) 2019 Richard "Shred" Körber
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

from struct import unpack

def disassemble(data, pc, org=0):
    step = 0
    ix = False
    iy = False
    iindex = None

    while pc + step < len(data):
        op = data[pc + step]
        step += 1
        if op == 0xDD:
            op2 = data[pc + step]
            if op2 == 0x00:
                step += 1
                ins = "exit"        # cspect emulator pseudo command
                break
            if op2 == 0x01:
                step += 1
                ins = "break"       # cspect emulator pseudo command
                break
            ix = True
            iy = False
        elif op == 0xFD:
            iy = True
            ix = False
        elif op == 0xED:
            ix = False
            iy = False
            op = data[pc + step]
            step += 1
            ins = decodeEd(op)
            break
        elif op == 0xCB:
            if ix or iy:
                iindex = unpack('b', data[pc + step:pc + step + 1])[0]
                step += 1
            op = data[pc + step]
            step += 1
            if ix or iy:
                ins = decodeCbWithIndex(op)
            else:
                ins = decodeCb(op)
            break
        else:
            if op == 0xEB:
                ix = False
                iy = False
            ins = INSTRUCTIONS[op]
            break

    if ix:
        if '(HL)' in ins and ins != 'jp (HL)':
            if iindex is None:
                iindex = unpack('b', data[pc + step:pc + step + 1])[0]
                step += 1
            ins = ins.replace('(HL)', '(IX%+d)' % (iindex))
        else:
            ins = ins.replace('HL', 'IX').replace('H', 'IXH').replace('L', 'IXL')
        ins = ins.replace('##', '**')

    if iy:
        if '(HL)' in ins and ins != 'jp (HL)':
            if iindex is None:
                iindex = unpack('b', data[pc + step:pc + step + 1])[0]
                step += 1
            ins = ins.replace('(HL)', '(IY%+d)' % (iindex))
        else:
            ins = ins.replace('HL', 'IY').replace('H', 'IYH').replace('L', 'IYL')
        ins = ins.replace('##', '**')

    ins = ins.lower()

    if '$' in ins:
        val = unpack('B', data[pc + step:pc + step + 1])[0]
        ins = ins.replace('$', '$%02X' % (val))
        step += 1

    if '^^' in ins:
        raw = data[pc + step:pc + step + 2]
        if -2048 <= unpack('>h', raw)[0] <= 2048:
            ins = ins.replace('^^', '%d' % (unpack('>h', raw)[0]))
        else:
            ins = ins.replace('^^', '$%04X' % (unpack('>H', raw)[0]))
        step += 2

    if '##' in ins:
        raw = data[pc + step:pc + step + 2]
        if -2048 <= unpack('<h', raw)[0] <= 2048:
            ins = ins.replace('##', '%d' % (unpack('<h', raw)[0]))
        else:
            ins = ins.replace('##', '$%04X' % (unpack('<H', raw)[0]))
        step += 2

    if '#' in ins:
        val = unpack('b', data[pc + step:pc + step + 1])[0]
        ins = ins.replace('#', '%d' % (val))
        step += 1

    if '**' in ins:
        val = unpack('<H', data[pc + step:pc + step + 2])[0]
        ins = ins.replace('**', '$%04X' % (val))
        step += 2

    if '*' in ins:
        val = unpack('B', data[pc + step:pc + step + 1])[0]
        ins = ins.replace('*', '$%02X' % (val))
        step += 1

    if '%' in ins:
        val = unpack('b', data[pc + step:pc + step + 1])[0]
        ins = ins.replace('%', '$%04X' % (org + pc + val + step + 1))
        step += 1

    return (ins, step)

def decodeEd(op):
    ins = None
    if 0x20 <= op < 0x40:
        ins = INSTRUCTIONS_ED_2[op - 0x20] # ZX Spectrum Next op codes
    elif 0x40 <= op < 0x80:
        ins = INSTRUCTIONS_ED_4[op - 0x40]
    elif 0x90 <= op < 0xA0:
        ins = INSTRUCTIONS_ED_9[op - 0x90] # ZX Spectrum Next op codes
    elif 0xA0 <= op < 0xC0:
        ins = INSTRUCTIONS_ED_A[op - 0xA0]
    elif op == 0x8A:
        ins = 'push ^^'     # ZX Spectrum Next op code
    if ins is None:
        ins = '???'
    return ins

def decodeCb(op):
    if op < 0x40:
        return '%s %s' % (INSTRUCTIONS_CB[(int)(op / 8)], REGISTER[op % 8])

    if 0x40 <= op < 0x80:
        ins = 'bit %d,%s'
    elif 0x80 <= op < 0xC0:
        ins = 'res %d,%s'
    else:
        ins = 'set %d,%s'
    return ins % ((op / 8) % 8, REGISTER[op % 8])

def decodeCbWithIndex(op):
    bit = (op / 8) % 8
    register = op % 8

    if op < 0x40:
        if register == 6:
            return '%s %s' % (INSTRUCTIONS_CB[(int)(op / 8)], REGISTER[register])
        else:
            return '%s (HL),%s' % (INSTRUCTIONS_CB[(int)(op / 8)], REGISTER[register])

    if 0x40 <= op < 0x80:
        return 'bit %d,(HL)' % (bit)
    elif 0x80 <= op < 0xC0:
        if register == 6:
            return 'res %d,(HL)' % (bit)
        else:
            return 'res %d,(HL),%s' % (bit, REGISTER[register])
    else:
        if register == 6:
            return 'set %d,(HL)' % (bit)
        else:
            return 'set %d,(HL),%s' % (bit, REGISTER[register])

# Placeholders:
#  ## -> 16 bit signed decimal
#  #  ->  8 bit signed decimal
#  ** -> 16 bit unsigned hex
#  *  ->  8 bit unsigned hex
#  %  ->  8 bit relative address
#  $  ->  8 bit ZX Spectrum Next register address
#  ^^ -> 16 bit signed decimal, big endian (ZX Spectrum Next proprietary)

INSTRUCTIONS = [
    'nop',          # 00
    'ld BC,##',     # 01
    'ld (BC),A',    # 02
    'inc BC',       # 03
    'inc B',        # 04
    'dec B',        # 05
    'ld B,#',       # 06
    'rlca',         # 07
    "ex AF,AF'",    # 08
    'add HL,BC',    # 09
    'ld A,(BC)',    # 0A
    'dec BC',       # 0B
    'inc C',        # 0C
    'dec C',        # 0D
    'ld C,#',       # 0E
    'rrca',         # 0F
    'djnz %',       # 10
    'ld DE,##',     # 11
    'ld (DE),A',    # 12
    'inc DE',       # 13
    'inc D',        # 14
    'dec D',        # 15
    'ld D,#',       # 16
    'rla',          # 17
    'jr %',         # 18
    'add HL,DE',    # 19
    'ld A,(DE)',    # 1A
    'dec DE',       # 1B
    'inc E',        # 1C
    'dec E',        # 1D
    'ld E,#',       # 1E
    'rra',          # 1F
    'jr nz,%',      # 20
    'ld HL,##',     # 21
    'ld (**),HL',   # 22
    'inc HL',       # 23
    'inc H',        # 24
    'dec H',        # 25
    'ld H,#',       # 26
    'daa',          # 27
    'jr z,%',       # 28
    'add HL,HL',    # 29
    'ld HL,(**)',   # 2A
    'dec HL',       # 2B
    'inc L',        # 2C
    'dec L',        # 2D
    'ld L,#',       # 2E
    'cpl',          # 2F
    'jr nc,%',      # 30
    'ld SP,**',     # 31
    'ld (**),A',    # 32
    'inc SP',       # 33
    'inc (HL)',     # 34
    'dec (HL)',     # 35
    'ld (HL),#',    # 36
    'scf',          # 37
    'jr c,%',       # 38
    'add HL,SP',    # 39
    'ld A,(**)',    # 3A
    'dec SP',       # 3B
    'inc A',        # 3C
    'dec A',        # 3D
    'ld A,#',       # 3E
    'ccf',          # 3F
    'ld B,B',       # 40
    'ld B,C',       # 41
    'ld B,D',       # 42
    'ld B,E',       # 43
    'ld B,H',       # 44
    'ld B,L',       # 45
    'ld B,(HL)',    # 46
    'ld B,A',       # 47
    'ld C,B',       # 48
    'ld C,C',       # 49
    'ld C,D',       # 4A
    'ld C,E',       # 4B
    'ld C,H',       # 4C
    'ld C,L',       # 4D
    'ld C,(HL)',    # 4E
    'ld C,A',       # 4F
    'ld D,B',       # 50
    'ld D,C',       # 51
    'ld D,D',       # 52
    'ld D,E',       # 53
    'ld D,H',       # 54
    'ld D,L',       # 55
    'ld D,(HL)',    # 56
    'ld D,A',       # 57
    'ld E,B',       # 58
    'ld E,C',       # 59
    'ld E,D',       # 5A
    'ld E,E',       # 5B
    'ld E,H',       # 5C
    'ld E,L',       # 5D
    'ld E,(HL)',    # 5E
    'ld E,A',       # 5F
    'ld H,B',       # 60
    'ld H,C',       # 61
    'ld H,D',       # 62
    'ld H,E',       # 63
    'ld H,H',       # 64
    'ld H,L',       # 65
    'ld H,(HL)',    # 66
    'ld H,A',       # 67
    'ld L,B',       # 68
    'ld L,C',       # 69
    'ld L,D',       # 6A
    'ld L,E',       # 6B
    'ld L,H',       # 6C
    'ld L,L',       # 6D
    'ld L,(HL)',    # 6E
    'ld L,A',       # 6F
    'ld (HL),B',    # 70
    'ld (HL),C',    # 71
    'ld (HL),D',    # 72
    'ld (HL),E',    # 73
    'ld (HL),H',    # 74
    'ld (HL),L',    # 75
    'halt',         # 76
    'ld (HL),A',    # 77
    'ld A,B',       # 78
    'ld A,C',       # 79
    'ld A,D',       # 7A
    'ld A,E',       # 7B
    'ld A,H',       # 7C
    'ld A,L',       # 7D
    'ld A,(HL)',    # 7E
    'ld A,A',       # 7F
    'add A,B',      # 80
    'add A,C',      # 81
    'add A,D',      # 82
    'add A,E',      # 83
    'add A,H',      # 84
    'add A,L',      # 85
    'add A,(HL)',   # 86
    'add A,A',      # 87
    'adc A,B',      # 88
    'adc A,C',      # 89
    'adc A,D',      # 8A
    'adc A,E',      # 8B
    'adc A,H',      # 8C
    'adc A,L',      # 8D
    'adc A,(HL)',   # 8E
    'adc A,A',      # 8F
    'sub B',        # 90
    'sub C',        # 91
    'sub D',        # 92
    'sub E',        # 93
    'sub H',        # 94
    'sub L',        # 95
    'sub (HL)',     # 96
    'sub A',        # 97
    'sbc A,B',      # 98
    'sbc A,C',      # 99
    'sbc A,D',      # 9A
    'sbc A,E',      # 9B
    'sbc A,H',      # 9C
    'sbc A,L',      # 9D
    'sbc A,(HL)',   # 9E
    'sbc A,A',      # 9F
    'and B',        # A0
    'and C',        # A1
    'and D',        # A2
    'and E',        # A3
    'and H',        # A4
    'and L',        # A5
    'and (HL)',     # A6
    'and A',        # A7
    'xor B',        # A8
    'xor C',        # A9
    'xor D',        # AA
    'xor E',        # AB
    'xor H',        # AC
    'xor L',        # AD
    'xor (HL)',     # AE
    'xor A',        # AF
    'or B',         # B0
    'or C',         # B1
    'or D',         # B2
    'or E',         # B3
    'or H',         # B4
    'or L',         # B5
    'or (HL)',      # B6
    'or A',         # B7
    'cp B',         # B8
    'cp C',         # B9
    'cp D',         # BA
    'cp E',         # BB
    'cp H',         # BC
    'cp L',         # BD
    'cp (HL)',      # BE
    'cp A',         # BF
    'ret nz',       # C0
    'pop BC',       # C1
    'jp nz,**',     # C2
    'jp **',        # C3
    'call nz,**',   # C4
    'push BC',      # C5
    'add A,#',      # C6
    'rst 00h',      # C7
    'ret z',        # C8
    'ret',          # C9
    'jp z,**',      # CA
    None,           # CB: Bit operations
    'call z,**',    # CC
    'call **',      # CD
    'adc A,#',      # CE
    'rst 08h',      # CF
    'ret nc',       # D0
    'pop DE',       # D1
    'jp nc,**',     # D2
    'out (*),A',    # D3
    'call nc,**',   # D4
    'push DE',      # D5
    'sub #',        # D6
    'rst 10h',      # D7
    'ret c',        # D8
    'exx',          # D9
    'jp c,**',      # DA
    'in A,(*)',     # DB
    'call c,**',    # DC
    None,           # DD: IX registers
    'sbc A,#',      # DE
    'rst 18h',      # DF
    'ret po',       # E0
    'pop HL',       # E1
    'jp po,**',     # E2
    'ex (SP),HL',   # E3
    'call po,**',   # E4
    'push HL',      # E5
    'and *',        # E6
    'rst 20h',      # E7
    'ret pe',       # E8
    'jp (HL)',      # E9
    'jp pe,**',     # EA
    'ex DE,HL',     # EB
    'call pe,**',   # EC
    None,           # ED: Extended instructions
    'xor *',        # EE
    'rst 28h',      # EF
    'ret p',        # F0
    'pop AF',       # F1
    'jp p,**',      # F2
    'di',           # F3
    'call p,**',    # F4
    'push AF',      # F5
    'or *',         # F6
    'rst 30h',      # F7
    'ret m',        # F8
    'ld SP,HL',     # F9
    'jp m,**',      # FA
    'ei',           # FB
    'call m,**',    # FC
    None,           # FD: IY registers
    'cp #',         # FE
    'rst 38h'       # FF
]

# These are ZX Spectrum Next proprietary op codes!
INSTRUCTIONS_ED_2 = [
    None,           # 20
    None,           # 21
    None,           # 22
    'swapnib',      # 23
    'mirror A',     # 24
    None,           # 25
    None,           # 26
    'test #',       # 27
    'bsla DE,B',    # 28
    'bsra DE,B',    # 29
    'bsrl DE,B',    # 2A
    'bsrf DE,B',    # 2B
    'brlc DE,B',    # 2C
    None,           # 2D
    None,           # 2E
    None,           # 2F
    'mul D,E',      # 30
    'add HL,A',     # 31
    'add DE,A',     # 32
    'add BC,A',     # 33
    'add HL,##',    # 34
    'add DE,##',    # 35
    'add BC,##',    # 36
    None,           # 37
    None,           # 38
    None,           # 39
    None,           # 3A
    None,           # 3B
    None,           # 3C
    None,           # 3D
    None,           # 3E
    None,           # 3F
]

INSTRUCTIONS_ED_4 = [
    'in B,(C)',     # 40
    'out (C),B',    # 41
    'sbc HL,BC',    # 42
    'ld (**),BC',   # 43
    'neg',          # 44
    'retn',         # 45
    'im 0',         # 46
    'ld I,A',       # 47
    'in C,(C)',     # 48
    'out (C),C',    # 49
    'adc HL,BC',    # 4A
    'ld BC,(**)',   # 4B
    'neg',          # 4C    Illegal opcode
    'reti',         # 4D
    None,           # 4E
    'ld R,A',       # 4F
    'in D,(C)',     # 50
    'out (C),D',    # 51
    'sbc HL,DE',    # 52
    'ld (**),DE',   # 53
    'neg',          # 54    Illegal opcode
    'retn',         # 55
    'im 1',         # 56
    'ld A,I',       # 57
    'in E,(C)',     # 58
    'out (C),E',    # 59
    'adc HL,DE',    # 5A
    'ld DE,(**)',   # 5B
    'neg',          # 5C    Illegal opcode
    'retn',         # 5D
    'im 2',         # 5E
    'ld A,R',       # 5F
    'in H,(C)',     # 60
    'out (C),H',    # 61
    'sbc HL,HL',    # 62
    'ld (**),HL',   # 63    Illegal opcode
    'neg',          # 64    Illegal opcode
    'retn',         # 65
    'im 0',         # 66
    'rrd',          # 67
    'in L,(C)',     # 68
    'out (C),L',    # 69
    'adc HL,HL',    # 6A
    'ld HL,(**)',   # 6B    Illegal opcode
    'neg',          # 6C    Illegal opcode
    'retn',         # 6D
    None,           # 6E
    'rld',          # 6F
    'in (C)',       # 70    Illegal opcode
    'out (C),0',    # 71    Illegal opcode
    'sbc HL,SP',    # 72
    'ld (**),SP',   # 73
    'neg',          # 74    Illegal opcode
    'retn',         # 75
    'im 1',         # 76
    None,           # 77
    'in A,(C)',     # 78
    'out (C),A',    # 79
    'adc HL,SP',    # 7A
    'ld SP,(**)',   # 7B
    'neg',          # 7C    Illegal opcode
    'retn',         # 7D
    'im 2',         # 7E
    None,           # 7F
]

# These are ZX Spectrum Next proprietary op codes!
INSTRUCTIONS_ED_9 = [
    'outinb',       # 90
    'nextreg $,#',  # 91
    'nextreg $,A',  # 92
    'pixeldn',      # 93
    'pixelad',      # 94
    'setae',        # 95
    None,           # 96
    None,           # 97
    'jp (C)',       # 98
    None,           # 99
    None,           # 9A
    None,           # 9B
    None,           # 9C
    None,           # 9D
    None,           # 9E
    None,           # 9F
]

INSTRUCTIONS_ED_A = [
    'ldi',          # A0
    'cpi',          # A1
    'ini',          # A2
    'outi',         # A3
    'ldix',         # A4 - ZX Spectrum Next op code
    'ldws',         # A5 - ZX Spectrum Next op code
    None,           # A6
    None,           # A7
    'ldd',          # A8
    'cpd',          # A9
    'ind',          # AA
    'outd',         # AB
    'lddx',         # AC - ZX Spectrum Next op code
    None,           # AD
    None,           # AE
    None,           # AF
    'ldir',         # B0
    'cpir',         # B1
    'inir',         # B2
    'otir',         # B3
    'ldirx',        # B4 - ZX Spectrum Next op code
    None,           # B5
    "ldirscale",    # B6 - ZX Spectrum Next op code (considered)
    'ldpirx',       # B7 - ZX Spectrum Next op code
    'lddr',         # B8
    'cpdr',         # B9
    'indr',         # BA
    'otdr',         # BB
    'lddrx',        # BC - ZX Spectrum Next op code
    None,           # BD
    None,           # BE
    None,           # BF
]

INSTRUCTIONS_CB = [
    'rlc',
    'rrc',
    'rl',
    'rr',
    'sla',
    'sra',
    'sll',          # Illegal opcode
    'srl',
]

REGISTER = [
    'B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A'
]
