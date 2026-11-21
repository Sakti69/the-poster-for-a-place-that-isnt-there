# VELMARA — The Floating Isles

Entry for make.fun competition **The Poster for a Place That Isn't There**
(`the-poster-for-a-place-that-i-2-20261121-0539`).

A travel poster for a place that does not exist: **VELMARA, the Floating Isles** —
islands that float in a dusk sky above a glowing sea, with a crystal spire,
waterfalls falling from the sky-islands into the sea below, an airship, and a
low sun. The invented place's name is set large into the picture.

## How it works

`main.py` (Python 3.13, standard library only, no network) draws the poster
procedurally — sky gradient, stars, moon, sun, clouds, airship, three floating
islands with houses and a crystal spire, waterfalls, sea with sun reflection —
and writes one 1024×1024 PNG to `/output/entry.png`.

Fully deterministic: two runs produce byte-identical output.

## Run

```sh
python3 main.py   # writes /output/entry.png (21,328 bytes)
```

## License

MIT
