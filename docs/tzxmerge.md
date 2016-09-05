# `tzxmerge`

Merges multiple TZX files into a single TZX file.

Multiple TZX files can also just be concatenated (e.g. `cat file1.tzx file2.tzx > files.tzx`), but this will add an unused "glue" block. `tzxmerge` merges TZX files without a "glue" block. It also fails if one of the files is not a TZX file.

## Usage

```
tzxmerge [-h] [--to TARGET] files [files ...]
```

* `files`: TZX files to merge.
* `-o`, `--to`: Target file. If omitted, `stdout` is used.
* `-h`, `--help`: Show help message and exit.

## Example

```
tzxmerge -o demo.tzx demo-loader.tzx demo-screen.tzx demo-binaries.tzx
```

Creates a `demo.tzx` file consisting of `demo-loader.tzx`, `demo-screen.tzx` and `demo-binaries.tzx`.
