# Profile artwork

These illustrations are decorative profile artwork, not recordings of a robot experiment or project results. The SVG and Python source are kept here so the existing animations can be changed without an external image service.

Regenerate the four looping GIFs, their still frames, and the interest badges:

```bash
python3 tools/generate_visuals.py
```

The script uses Pillow, PyGObject, GdkPixbuf with an SVG loader, and DejaVu Sans fonts. On Ubuntu these are provided by `python3-pil`, `python3-gi`, `gir1.2-gdkpixbuf-2.0`, `librsvg2-common`, and `fonts-dejavu-core`.

`assets/banner.svg` is the editable source for the header's static layout. The header embeds the yellow/red Better Call Jerry logo on the left and the moving arm on the right. The typing animation opens with “Your robot has the right to remain stable.” Each animation uses a stable palette and runs locally from the repository; no API keys or scheduled workflows are needed for display or animation rendering.

## Better Call Jerry logo

`assets/better-call-jerry-logo.png` is a personal adaptation of the Better Call Saul title logo. The yellow lettering and balance scales come from the [reference SVG](https://en.wikipedia.org/wiki/File:Better_Call_Saul_logo.svg). The red name was redrawn as **Jerry** using the imagegen CLI with `gpt-image-2`, then composited with the original yellow shapes. The new lettering matches the reference's brush-script style; it is not a verified original font file.

The final artwork uses yellow `#FFFF33`, red `#FF3333`, and black `#000000`, with a small margin for display. It is a local PNG and needs no external image service to display.

The header generator extracts transparency from this black-backed logo, so the lettering blends into the navy background without a separate rectangular panel.

## Jerry's pixel room

`assets/jerry-room-base.png` is a still adaptation of the room GIF supplied by the profile owner. The base was edited with the imagegen CLI and `gpt-image-2`, then normalized to a 240×135 pixel grid. Jerry, Tom collectibles, cheese, pink neon balance scales, a red telephone and lawyer's briefcases personalize the reference room while preserving its dark navy and magenta atmosphere.

Rebuild its looping GIF from the saved base, without an API call:

```bash
python3 tools/animate_room.py
```

The renderer uses Pillow, a shared palette and nearest-neighbor scaling. It exports `assets/jerry-room.gif` at 960×540, with a still preview in `assets/jerry-room-still.png`. The loop lasts 4.9 seconds, matching the reference's 49 frames at 100 ms per frame.
