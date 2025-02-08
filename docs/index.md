# tzxtools

This is a collection of command line tools for processing TZX files.

TZX is a common file format for preserving computer tapes of the ZX Spectrum, but also Amstrad CPC and C64. `tzxtools` mainly supports ZX Spectrum TZX files, but raw file operations can be applied on any TZX file. It also supports TSX files, which are mainly used for MSX.

## Features

* Convert your old ZX Spectrum tape recordings into TZX files.
* List, split, merge, and divide the blocks inside TZX files.
* Extract binary content from TZX blocks.
* Read hex dumps, disassembled Z80 machine code, or ZX Spectrum BASIC code.
* Convert ZX Spectrum screens to PNG files.
* Generate TAP files for ZX Spectrum Next and some emulators.
* Disassembler also supports all undocumented Z80 instructions and Z80N (ZX Spectrum Next) instructions.
* Also supports TSX Kansas City Standard blocks.
* All tools can also read TAP files.

## Installation

All the _tzxtools_ are written in Python 3.

```sh
pip install tzxtools
```

On MacOS X, [PortAudio](http://www.portaudio.com/) needs to be installed before:

```sh
brew install portaudio
pip3 install tzxtools
```

## The Tools

* [`tzxcat`](tzxcat.md) - Extracts data from a TZX file. Optionally disassembles, hex dumps or converts blocks to PNG.
* [`tzxcleanup`](tzxcleanup.md) - Removes all clutter and leaves a clean tape file.
* [`tzxcut`](tzxcut.md) - Cuts blocks from a TZX file.
* [`tzxls`](tzxls.md) - Lists the contents of a TZX file.
* [`tzxmerge`](tzxmerge.md) - Concatenates multiple TZX files into one file.
* [`tzxplay`](tzxplay.md) - Plays back a TZX file for loading into real hardware.
* [`tzxsplit`](tzxsplit.md) - Splits a TZX file into separate programs.
* [`tzxtap`](tzxtap.md) - Converts a TZX file to TAP file format.
* [`tzxwav`](tzxwav.md) - Converts WAV file ZX Spectrum tape recordings to TZX files.

## TZX and TSX File Format References

The TZX File Format is specified at [World of Spectrum](https://www.worldofspectrum.org/TZXformat.html).

The TSX "ID 4B - Kansas City Standard" block is not a part of the specification. A documentation can be found at the [makeTSX wiki](https://github.com/nataliapc/makeTSX/wiki/Tutorial-How-to-generate-TSX-files#14-the-new-4b-block).

## Open Source

_tzxtools_ is open source software. The source code is available [at Codeberg](https://codeberg.org/shred/tzxtools), and is distributed under the terms of [GNU General Public License (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.en.html#content).
