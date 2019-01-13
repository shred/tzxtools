# `tzxtap`

Converts a TZX file to a TAP file.

This tool is useful to convert TZX files to the TAP file format. Some emulators or computers like the _ZX Spectrum Next_ are unable to read TZX files, but accept the simpler and more restricted TAP file format. This tool converts a TZX file into this format.

Note that only Standard Speed Data Blocks can be used in TAP files. `tzxtap` stops with an error if it discovers other block types in the TZX file, unless the `--ignore` option is set.


## Usage

```
tzxtap [-h] [-o TARGET] [-i] [file]
```

* `file`: TZX file to read from, or `stdin` if not given.
* `-o`, `--to`: Target TAP file to write. If omitted, `stdout` is used.
* `-i`, `--ignore`: Ignore blocks that cannot be stored into a TAP file.
* `-h`, `--help`: Show help message and exit.

## Example

```
tzxtap -o tape.tap tape.tzx
```

Read `tape.tzx` and generate a `tape.tap` file from its Standard Speed Data Blocks.

```
tzxtap --ignore -o tape.tap
```

Like above, but ignore all blocks that cannot be used in TAP files.
