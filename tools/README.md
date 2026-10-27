# Profile artwork

These original illustrations are decorative profile artwork, not recordings of a robot experiment or project results. The SVG and Python source are kept here so the visuals can be changed without an external image service.

Regenerate the four looping GIFs, their still frames, and the interest badges:

```bash
python3 tools/generate_visuals.py
```

The script uses Pillow, PyGObject, GdkPixbuf with an SVG loader, and DejaVu Sans fonts. On Ubuntu these are provided by `python3-pil`, `python3-gi`, `gir1.2-gdkpixbuf-2.0`, `librsvg2-common`, and `fonts-dejavu-core`.

`assets/banner.svg` is the editable source for the header's static layout. All animations have a shared color palette and run locally from the repository; no API keys or scheduled workflows are needed.

## Better Call Jerry logo

`assets/better-call-jerry-logo.png` is a personal adaptation of the Better Call Saul title logo. The yellow lettering and balance scales come from the [reference SVG](https://en.wikipedia.org/wiki/File:Better_Call_Saul_logo.svg). The red name was redrawn as **Jerry** using the imagegen CLI with `gpt-image-2`, then composited with the original yellow shapes. The new lettering matches the reference's brush-script style; it is not a verified original font file.

The final artwork uses yellow `#FFFF33`, red `#FF3333`, and black `#000000`, with a small margin for display. It is a local PNG and needs no external image service to display.
