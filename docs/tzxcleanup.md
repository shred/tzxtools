# `tzxcleanup`

Removes all clutter from TZX files, and sets idealized timings for data blocks.

This is useful to clean up TZX files generated from a tape. Make sure that the data was saved in standard speed. This clean up procedure will remove all blocks that are used for hard copy protections (except of ZX Spectrum headerless files).

This tool is also useful if Fuse's `audio2tape` was invoked without `-r` option and thus created only Turbo Speed Data Blocks. They will be converted to Standard Speed Data Blocks unless they are too large.

Use this tool for ZX Spectrum TZX files only! Other machines may be unable to read the resulting file.

## Usage

```
tzxcleanup [-h] [-o TARGET] [-c] [file]
```

* `file`: TZX file to read from, or `stdin` if not given.
* `-o`, `--to`: Target file. If omitted, `stdout` is used.
* `-c`, `--stripcrc`: Also remove all data blocks with a bad CRC. They would usually lead to a "tape loading error".
* `-h`, `--help`: Show help message and exit.

## Example

```
tzxcleanup recording.tzx | tzxls -l
```

Shows the content of a cleaned-up `recording.tzx` file.

```
tzxcleanup -o game.tzx recording.tzx
```

Cleans up a raw `recording.tzx` file and writes it to `game.tzx`.
