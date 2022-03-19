# `tzxls`

Lists the contents of a TZX file.

Ths tool shows the block numbers, block types and some block contents of a TZX file.

For ZX Spectrum TZX files, it also shows header contents (like program names or data types). Note that CRC checks only apply for ZX Spectrum files. For other machines, this tool will always report false CRC errors.

This tool also accepts TAP files. They are converted to TZX format internally.

## Usage

```
tzxls [-h] [-s] [-v] file [file ...]
```

* `file`: TZX file or files to read from, or `stdin` if not given.
* `-s`, `--short`: Only shows the names found in ZX Spectrum file headers.
* `-h`, `--help`: Show help message and exit.
* `-v`, `--verbose`: Show more details about each block, if available.

## Example

```
tzxls tape.tzx
```

Lists all the TZX file blocks of `tape.tzx`.

```
tzxls -s tape.tzx
```
Lists the names of all the ZX Spectrum program and data files found on the `tape.tzx`.

```
tzxls -v tape.tzx
```

Lists all the TZX file blocks of `tape.tzx`, and shows details about each block.
