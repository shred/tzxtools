# `tzxcat`

Extracts the binary content of TZX data blocks to a file.

This tool is useful to migrate tape computer files to modern computers.

It also brings a set of converters to BASIC, assembler, image (PNG), plain text and hex dump.

## Usage

```
tzxcat [-h] [-b NR] [-o TARGET] [-s BYTES] [-l BYTES]
       [-t] [-B] [-A] [-S] [-d] [-O BASE] [file]
```

* `file`: TZX file to read from, or `stdin` if not given.
* `-o`, `--to`: Target file. If omitted, `stdout` is used.
* `-b`, `--block`: Only extract the TZX block with the given block number. If omitted, all data blocks are concatenated to a single output stream. The selected block must be a data block. If the block has a bad CRC, a warning is printed, but the content is extracted nevertheless.
* `-s`, `--skip`: Skip the given number of bytes before output. If omitted, nothing is skipped. If it exceeds the block length, an empty block is written.
* `-l`, `--length`: Limit the output to the given number of bytes. The rest of the block is written if this parameter is omitted or if it exceeds the block length.
* `-h`, `--help`: Show help message and exit.

A converter can be applied to the output. If no converter is chosen, the output is just the binary content of the selected block. Available converters are:

* `-t`, `--text`: Convert ZX Spectrum text to UTF-8.
* `-B`, `--basic`: Convert ZX Spectrum BASIC to plain UTF-8 text. The result is what you would see on the screen after a `LIST` command. Inline attribute changes are ignored though.
* `-A`, `--assembler`: Disassemble the block, using a simple Z80 disassembler. Undocumented Z80 op codes and ZX Spectrum Next op codes are supported. Note that ZX Spectrum Next op codes are still subject to change.
* `-S`, `--screen`: Convert a ZX Spectrum SCREEN$ to PNG. It is recommended to select the SCREEN block using the `--block` option.
* `-d`, `--dump`: Generate a hex dump of the block contents.

Additional converter options:

* `-O`, `--org`: Define the base address for disassembling. If not given, the starting address given in the previous `Bytes` header is used automatically.

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
