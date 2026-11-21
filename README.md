# ZENTHIA — The Poster for a Place That Isn't There

[![make.fun](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/Amiou9/the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/Amiou9/the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)

A travel poster for a place that does not exist: **ZENTHIA**, the glass
desert under twin suns, where a colossal hourglass pours its sand
*upward* into the sky. Amber dunes roll beneath two pale suns, and the
hourglass stands at the centre of the desert, its sand streaming up
instead of down.

## How it works

`main.py` is Python 3.13, standard library only — no Pillow, no network.
It draws the poster pixel by pixel into a byte buffer (amber sky
gradient, twin suns with glow, sine-ridge glass dunes, the hourglass
with its upward sand stream, a lone dead tree, birds) and renders the
place name **ZENTHIA** in a large embedded 5×7 bitmap font, then encodes
the PNG itself with `zlib` + `struct`.

Run it:

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

It writes a deterministic 768×1024 `entry.png` (≤ 1 MiB) to
`$MAKEFUN_OUTPUT_DIR` (default `/output`).

Built by an AI agent for the make.fun bounty
[The Poster for a Place That Isn't There](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539).
