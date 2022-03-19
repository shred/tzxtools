# `tzxcat`

Extracts the binary content of TZX data blocks to a file.

This tool is useful to migrate tape computer files to modern computers.

It also brings a set of converters to ZX Spectrum BASIC, assembler, ZX Spectrum screens, plain text and hex dump.

This tool also accepts TAP files. They are converted to TZX format internally.

## Usage

```
tzxcat [-h] [-b NR] [-o TARGET] [-s BYTES] [-l BYTES]
       [-t] [-B] [-A] [-S] [-d] [-O BASE] [file]
```

* `file`: TZX file to read from, or `stdin` if not given.
* `-o`, `--to`: Target file. If omitted, `stdout` is used.
* `-b`, `--block`: Only extract the TZX block with the given block number. If omitted, all data blocks are concatenated to a single output stream. The selected block must be a data block. If the block has a bad CRC, a warning is printed, but the content is extracted nevertheless. If this is not a ZX Spectrum block, a false CRC error is always reported and can be ignored.
* `-s`, `--skip`: Skip the given number of bytes before output. If omitted, nothing is skipped. If it exceeds the block length, an empty block is written.
* `-l`, `--length`: Limit the output to the given number of bytes. The rest of the block is written if this parameter is omitted or if it exceeds the block length.
* `-h`, `--help`: Show help message and exit.

A converter can be applied to the output. If no converter is chosen, the output is just the binary content of the selected block. Available converters are:

* `-t`, `--text`: Convert ZX Spectrum text to plain text.
* `-B`, `--basic`: Convert ZX Spectrum BASIC to plain text. The result is what you would see on the screen after a `LIST` command. Inline attribute changes are ignored though.
* `-A`, `--assembler`: Disassemble the block, using a simple Z80 disassembler. Undocumented Z80 op codes and Z80N (ZX Spectrum Next) op codes are supported. The disassembler also supports the `exit` and `break` pseudo op codes of the #CSpect emulator.
* `-S`, `--screen`: Convert a ZX Spectrum SCREEN$ to PNG. It is recommended to select the SCREEN block using the `--block` option.
* `-d`, `--dump`: Generate a hex dump of the block contents.

Additional converter options:

* `-O`, `--org`: Define the base address for hex dumps and disassembled code. If not given, the starting address given in the previous `Bytes` header is used automatically. If there is no such header, 0 is assumed as base address.

Converters use your system's encoding as target encoding. If your system does not use Unicode, the presence of some special characters may lead to an error.

## Example

```
tzxcat --block 4 --to screen.scr game.tzx
```

Reads the `game.tzx` file and copies the binary contents of the 4th block to `screen.scr`.

```
tzxcat --block 4 --screen --to screen.png game.tzx
```

The same as above, but now the screen is converted to PNG.

```
tzxcat --block 4 --text sources.tzx
```

Dumps block 4 in a (more or less) readable plain text format to stdout.

```
tzxcat --block 4 --dump sources.tzx
```

The same as above, but dumps block 4 as hex dump to stdout.

```
tzxcat --block 2 --basic sources.tzx
```

Shows block 2 as BASIC listing.

```
tzxcat --block 6 --assembler sources.tzx
```

Shows block 6 as disassembled machine code. The starting address of the `Bytes` header in block 5 is used automatically as the base address.

```
tzxcat --block 6 --assembler --org 32768 sources.tzx
```

The same as above, but 32768 is used as fixed base address.

## Supported Block Types

`tzxcat` can extract binary data from all block types containing actual data:

- 10 - Standard Speed Data Block
- 11 - Turbo Speed Data Block
- 14 - Pure Data Block
- 30 - Text description
- 31 - Message
- 35 - Custom info
- 4B - Kansas City Standard
