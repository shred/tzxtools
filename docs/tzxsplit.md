# `tzxsplit`

Splits a TZX file into its different programs.

This tool is useful to automatically split up a single TZX file of a mixed tape with different programs. `tzxsplit` searches for a ZX Spectrum "Program" block, and then extracts the program itself and all subsequent blocks up to the next "Program" block.

Each program and the subsequent blocks are written into a separate TZX file, which is named like the program itself. A number is added to the file name, in order to avoid file name collisions.

If the tape file should not start with a "Program", all blocks up to the first Program are stored into a TZX file called "preamble.tzx".

See also `tzxcut`.

This tool also accepts a TAP file. It is converted to TZX format internally.

## Usage

```
tzxsplit [-h] [-d TARGET] [-s] [file]
```

* `file`: TZX file to read from, or `stdin` if not given.
* `-d`, `--dir`: Target directory of the generated TZX files. If omitted, the current directory is used.
* `-s`, `--skip`: Instead of writing a preamble file, just skip all blocks up to the first program.
* `-1`, `--single`: Split at every loadable file instead of splitting at every program.
* `-h`, `--help`: Show help message and exit.

## Example

```
tzxsplit tape.tzx
```

Read `tape.tzx` and generate TZX files for all the programs (and the subsequent data blocks) found in it.
