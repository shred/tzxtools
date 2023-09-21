# Changelog

## v1.9.2 (2023-09-21)

* `tzxplay`: Fix crash on zero length wavelets

## v1.9.1 (2022-08-03)

* `tzxls`: Verbose option threw a Python error, fixed

## v1.9.0 (2022-06-03)

* `tzxtap`: Skip comment blocks, as the TAP file can be read without them

## v1.8.0 (2022-03-20)

* All tools can now also read TAP files
* Use sounddevice instead of pyaudio (which is not maintained any more)

## v1.7.0 (2021-02-28)

* Add new `tzxplay` tool for playing back TZX files
* `tzxcleanup`: Add `--headermustmatch` option (by @oxidaan)
* `tzxwav`: Verbose output shows tape time of each found block (idea by @oxidaan)

## v1.6.0 (2020-11-11)

* Fix `stdin` and `stdout` usage on Windows installations
* `tzxcat`: Also dump contents of deprecated C64 data blocks

## v1.5.0 (2020-05-29)

* `tzxls`: Add `--verbose` option to get more details about TZX blocks
* Add support for TSX Kansas City Standard blocks
* `tzxcat`: Also dump contents of TZX text description blocks

## v1.4.0 (2020-05-02)

* Add more Z80N and CSpect op codes to the disassembler
* Enhance `tzxwav` debug output

## v1.3.0 (2019-11-14)

* Fix broken raw binary output on `tzxcat`

## v1.2.0 (2019-01-13)

* `tzxcat`: Add `--screen` option, to convert a standard ZX Spectrum `SCREEN$` block to a PNG file
* `tzxcat`: Add `--org` option, to set the base address of dumps and disassembles. If not given, the base address of the previous `CODE` header is used
* `tzxcat`: Add `--assembler` option, which disassembles the machine code of a block
* `tzxcat`: Add `--dump` option, which creates a hex dump of the block content
* `tzxcat`: Add `--skip` and `--length` option to extract only parts of a block

## v1.1.0 (2018-08-30)

* Add `tzxtap` tool, it generates `tap` files from `tzx` files

## v1.0.1 (2018-08-23)

* First release
