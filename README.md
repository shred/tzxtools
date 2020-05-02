# tzxtools

This is a collection of command line tools for processing [TZX](http://www.worldofspectrum.org/TZXformat.html) files.

TZX is a common file format for preserving computer tapes of the ZX Spectrum, but also Amstrad CPC and C64. `tzxtools` mainly supports ZX Spectrum TZX files, but raw file operations can be applied on any TZX file.

## Features

* Convert your old ZX Spectrum tape recordings into TZX files.
* List, split, merge, and divide the blocks inside TZX files.
* Extract binary content from TZX blocks.
* Read hex dumps, disassembled Z80 machine code, or ZX Spectrum BASIC code.
* Convert ZX Spectrum screens to PNG files.
* Generate TAP files for ZX Spectrum Next and some emulators.
* Disassembler also supports all undocumented Z80 instructions and Z80N (ZX Spectrum Next) instructions.

## Installation

All the _tzxtools_ are written in Python 3.

```sh
pip install tzxtools
```

## Tools

* `tzxcat` - Extracts data from a TZX file. Optionally disassembles, hex dumps or converts blocks to PNG.
* `tzxcleanup` - Removes all clutter blocks and leaves a clean TZX file.
* `tzxcut` - Cuts blocks from a TZX file.
* `tzxls` - Lists the contents of a TZX file.
* `tzxmerge` - Concatenates multiple TZX files into one file.
* `tzxsplit` - Splits a TZX file into separate programs.
* `tzxtap` - Converts a TZX file to TAP file format.
* `tzxwav` - Converts WAV file ZX Spectrum tape recordings to TZX files.

See the [documentation](https://shredzone.org/docs/tzxtools/index.html) for how the tools are used.

## Contribute

* Fork the [Source code at GitHub](https://github.com/shred/tzxtools). Feel free to send pull requests.
* Found a bug? [File a bug report!](https://github.com/shred/tzxtools/issues)

## License

_tzxtools_ is open source software. The source code is distributed under the terms of [GNU General Public License (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.en.html#content).

## Acknowledgements

* I would like to thank all the people who keep the retro computing scene alive.
