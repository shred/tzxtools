# `tzxcat`

Extracts the binary content of TZX data blocks to a file.

This tool is useful to migrate tape computer files to modern computers.

## Usage

```
tzxcat [-h] [-b NR] [-o TARGET] [-t] [file]
```

* `file`: TZX file to read from, or `stdin` if not given.
* `-o`, `--to`: Target file. If omitted, `stdout` is used.
* `-b`, `--block`: Only extract the TZX block with the given block number. If omitted, all data blocks are concatenated to a single output stream. This must be a data block. If the block has a bad CRC, a warning is printed, but the content is extracted nevertheless.
* `-t`, `--text`: Convert a ZX Spectrum text to UTF-8 before output.
* `-h`, `--help`: Show help message and exit.

## Example

```
tzxcat -b 4 -o screen.scr game.tzx
```

Reads the `game.tzx` file and dumps the 4th block into `screen.scr`.

```
tzxcat -b 4 -t sources.tzx
```

Dumps block 4 in a (more or less) readable text format to stdout.
