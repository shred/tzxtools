# `tzxplay`

Plays back a TZX file.

This tool is useful to feed a real ZX Spectrum with a TZX file. It is played back via your system's audio output. Usually you would connect your ZX Spectrum to your computer's headphone output, and then play back the TZX file.

Optionally, a WAV file can be generated instead. You can store this WAV file on a portable media player, and then use the player to load files into your ZX Spectrum.

Playback can always be aborted by pressing Ctrl-C.

This tool also accepts a TAP file. It is converted to TZX format internally.

## Notes

* **TURN DOWN THE SYSTEM VOLUME FIRST!** The output signal is very loud, and may damage your speakers with its rectangle pulses. Make sure to turn down your system volume before using `tzxplay` for the first time.

* Do not compress the WAV file with a lossy format like mp3 or Ogg Vorbis. This may lead to tape loading errors. Remember that lossy compressors are optimized for human ears, not ZX Spectrum ears. Lossless formats like FLAC can be used, though.

* `tzxplay` supports the most commonly used blocks at the moment, so classic recordings and even many speedloaders can be played back. However, some very special data blocks and control blocks will be ignored, or lead to an error.

* The generated WAV file can become quite large, especially if the TZX file contains jumps or loops. Broken TZX files can even result in an endless loop. You can press Ctrl-C to abort `tzxplay`.

* Playback of C64 or Kansas City Standard blocks is not supported at the moment.

* You can use [`tzxcut`](tzxcut.md) to play only a subset of blocks from a TZX file (see example below).

## Usage

```
tzxplay [-h] [-o TARGET] [-v] [-s] [-K] [-r RATE] [-c CLOCK] [-S] [file]
```

* `file`: TZX file to read from, or `stdin` if not given.
* `-o`, `--to`: Create a WAV file instead of playing audio.
* `-v`, `--verbose`: Be verbose about what you are doing.
* `-s`, `--stop`: Stop playback on Stop-The-Tape blocks. By default, playback only stops when the end of the TZX file is reached.
* `-K`, `--48k`: Enable ZX Spectrum 48K mode. If set, playback stops on a 2A block ("Stop the tape if in 48K mode"). Use this option if you have a dual 48K/128K tape, and only want to load the ZX Spectrum 48K part.
* `-r`, `--rate`: Output sampling rate, default is 44100 Hz. Please use only common sampling rates like 22050, 32000, 44100, 48000. While `tzxplay` will accept other rates, they may result in playback problems.
* `-c`, `--clock`: Change reference Z80 CPU clock speed, in Hz. Default is 3500000. There is usually no need to change it.
* `-S`, `--sine`: By default `tzxplay` generates perfect rectangle pulses. They are optimal for loading, but do not sound really Spectrum-ish. With this option, the sine pulses of a classic tape recording are simulated.
* `-h`, `--help`: Show help message and exit.

## Example

```
tzxplay game.tzx
```

Read `game.tzx` and play it back via your computer's audio interface.

```
tzxplay -v game.tzx
```

Like above, but also shows what block is being processed.

```
tzxplay -o game.wav game.tzx
```

Generate a WAV file instead.

```
tzxcut -i games.tzx 0:5 | tzxplay
```

Only play back blocks 0 to 5 (inclusive).