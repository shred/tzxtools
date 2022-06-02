# `tzxtap`

Converts a TZX file to a TAP file.

This tool is useful to convert TZX files to the TAP file format. Some emulators or computers are unable to read TZX files, but accept TAP files. This tool converts a TZX file into this format.

TAP files are much simpler than TZX files, as they only support Standard Speed Data Blocks. TZX comment blocks will be skipped with a warning. Other TZX blocks (like those used by speedloaders) will result in an error, because they cannot be converted to the TAP format. You can enforce conversion by using the `--ignore` option, but it is very unlikely that the resulting TAP file can be loaded successfully.

This tool also accepts a TAP file, but will generate an identical TAP file from it.

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

Like above, but ignore all blocks that cannot be converted to TAP files.
