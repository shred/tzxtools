# tzxtools

This is a collection of command line tools for processing [TZX](http://www.worldofspectrum.org/TZXformat.html) files. TZX is a common file format for preserving computer tapes of the ZX Spectrum, but also Amstrad CPC and C64. All the _tzxtools_ are witten in Python 3.

## Installation

```sh
pip install tzxtools
```

## The Tools

* [`tzxcat`](tzxcat.md) - Extracts file data from a TZX file
* [`tzxcleanup`](tzxcleanup.md) - Removes all clutter and leaves a clean tape file
* [`tzxcut`](tzxcut.md) - Cuts blocks from a TZX file
* [`tzxls`](tzxls.md) - Shows the contents of a TZX file
* [`tzxmerge`](tzxmerge.md) - Concatenates multiple TZX files into one file
* [`tzxsplit`](tzxsplit.md) - Splits a TZX file into separate programs
* [`tzxtap`](tzxtap.md) - Converts a TZX file to a TAP file
* [`tzxwav`](tzxwav.md) - Converts WAV file tape recordings to TZX files

## Open Source

_tzxtools_ is open source software. The source code is available [at GitHub](https://github.com/shred/tzxtools), and is distributed under the terms of [GNU General Public License (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.en.html#content).
