# `tzxls`

Lists the contents of a TZX file.

Ths tool shows the block numbers, block types and some block contents of a TZX file.

## Usage

```
tzxls [-h] [-s] [file]
```

* `file`: TZX file to read from, or `stdin` if not given.
* `-s`, `--short`: Only shows the names found in ZX Spectrum file headers.
* `-h`, `--help`: Show help message and exit.

## Example

```
tzxls tape.tzx
```

Lists all the TZX file blocks of `tape.tzx`.

```
tzxls -s tape.tzx
```
Lists the names of all the ZX Spectrum program and data files found on the `tape.tzx`.
