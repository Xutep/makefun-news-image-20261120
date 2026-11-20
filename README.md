# news-image-20261120 — The World in One Image

Entry for the make.fun bounty
[`news-image-20261120`](https://make.fun/bounty/news-image-20261120):
sum up the world news of **Friday 20 November 2026** in one image.

## What it is

`main.py` (Python 3.13, standard library only, no network) draws a
1024x1024 newspaper front page and writes it to `/output/entry.png`:

- **Lead story** — the first-ever three-way summit of Trump, Xi and Putin
  in Shenzhen, China, and their joint peace declaration.
- **Six more stories** — the ICJ ruling that Myanmar committed genocide
  against the Rohingya; Trump pushing any Iran decision to 2027;
  Voyager 1 reaching one light-day from Earth; Cyclone Akvan bearing
  down on Odisha, India (300,000 evacuated); GTA 6 sales passing
  $1.8 billion; a Van Gogh selling for a record $190.4 million.

All drawing is done in code: a hand-written PNG encoder (zlib/struct),
a small canvas with rect/line/circle primitives, and an embedded 5x7
bitmap font. Two runs write byte-identical PNGs.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
```

## License

MIT — see `LICENSE`.
