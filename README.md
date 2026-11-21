# VELDARA — Valley of the Floating Lanterns

![bounty](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)
![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)
![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)

A travel poster for a place that does not exist. Veldara is a river
valley at dusk where hundreds of paper lanterns drift downstream
past a stone bridge and a small town with lit windows, under a low
moon and layered mountains.

## Run

```sh
python3 main.py
```

Writes `entry.png` (1024×1024 JPEG content, ~0.25 MB) to
`$MAKEFUN_OUTPUT_DIR`, `$OUTPUT_DIR`, or `./output/`.

The render is fully procedural (PIL only, no network, no downloads)
and deterministic: a fixed seed makes two runs byte-identical.
Fonts (DejaVu Serif / DejaVu Sans, freely licensed) are bundled in
`fonts/` so the program never touches system font paths.

## Files

- `main.py` — entrypoint, picks the output directory and saves the poster
- `draw.py` — the whole poster: dusk sky, mountains and mist, river,
  lanterns with bloom and reflections, bridge, town, type, frame, grain
- `fonts/` — bundled DejaVu fonts (free license)
