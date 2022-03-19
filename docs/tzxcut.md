# `tzxcut`

Cuts out blocks from a TZX file into a new TZX file.

This tool is useful to split the copy of a mixed tape into a separate TZX file for one of the programs.

See also `tzxsplit`.

This tool also accepts a TAP file. It is converted to TZX format internally.

## Usage

```
tzxcut [-h] [-i SOURCE] [-o TARGET] [-v] [blocks [blocks ...]]
```

* `blocks`: Block number, or range of block numbers, to keep in the output file. Use `tzxls` to find out the block numbers of a TZX file.
* `-i`, `--from`: TZX file to read from, or `stdin` if not given.
* `-o`, `--to`: Target file. If omitted, `stdout` is used.
* `-v`, `--invert`: Invert block matches. The given block numbers are not kept, but removed.
* `-h`, `--help`: Show help message and exit.

Blocks can be addressed in a single number or in a range:

* `13` - Keep block number 13.
* `4:8` - Keep block numbers 4 to 8 (inclusive).
* `3:` - Keep block numbers 3 and higher.
* `:4` - Keep the first blocks up to block 4 (inclusive).

Remember that blocks are counted starting from zero.

Negative block numbers are counted backwards from the last block:

* `-1` - Keep only the last block.
* `4:-2` - Keep block numbers from 4 up to the second to last block.
* `-4:` - Keep the last four blocks.
* `:-3` - Keep all the blocks up the third to last block.

If you use negative block numbers, it is wise to place a `--` at the command line before the block ranges, so negative block numbers are not interpreted as options (see example below).

## Example

```
tzxcut -i games.tzx -o first-game.tzx 0:5 7
```

Copies the blocks 0 to 5 (inclusive) and block 7 of `games.tzx` into a new file `first-game.tzx`.

```
tzxcut -i games.tzx -o first-game.tzx -- -5 -3:
```

Copies the fifth to last and the three last blocks of `games.tzx` into a new file `first-game.tzx`.
