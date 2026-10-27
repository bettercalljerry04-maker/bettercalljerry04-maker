# Profile artwork

These illustrations are decorative profile artwork, not recordings of a robot experiment or project results. The SVG and Python source are kept here so the existing animations can be changed without an external image service.

Regenerate the four looping GIFs, their still frames, and the interest badges:

```bash
python3 tools/generate_visuals.py
```

The script uses Pillow, PyGObject, GdkPixbuf with an SVG loader, and DejaVu Sans fonts. On Ubuntu these are provided by `python3-pil`, `python3-gi`, `gir1.2-gdkpixbuf-2.0`, `librsvg2-common`, and `fonts-dejavu-core`.

`assets/banner.svg` is the editable source for the header's static layout. The header (`assets/better-call-jerry-hero.gif`) embeds the yellow/red Better Call Jerry logo on the left and the moving arm on the right. The typing animation (`assets/robot-rights-typing.gif`) opens with “Your robot has the right to remain stable.” Each animation uses a stable palette and runs locally from the repository; no API keys or scheduled workflows are needed for display or animation rendering.

## Better Call Jerry logo

`assets/better-call-jerry-logo.png` is a personal adaptation of the Better Call Saul title logo. The yellow lettering and balance scales come from the [reference SVG](https://en.wikipedia.org/wiki/File:Better_Call_Saul_logo.svg). The red name was redrawn as **Jerry** using the imagegen CLI with `gpt-image-2`, then composited with the original yellow shapes. The new lettering matches the reference's brush-script style; it is not a verified original font file.

The final artwork uses yellow `#FFFF33`, red `#FF3333`, and black `#000000`, with a small margin for display. It is a local PNG and needs no external image service to display.

The header generator extracts transparency from this black-backed logo, so the lettering blends into the navy background without a separate rectangular panel.

## Jerry's pixel room

`assets/jerry-room-suit-base.png` is a still adaptation of the room GIF supplied by the profile owner. The base was edited with the imagegen CLI and `gpt-image-2`, then normalized to a 240×135 pixel grid. Jerry, Tom collectibles, cheese, pink neon balance scales, a red telephone and lawyer's briefcases personalize the reference room while preserving its dark navy and magenta atmosphere. The latest edit dresses Jerry in a charcoal suit, ivory shirt and burgundy tie. Only the outfit region was composited into the existing base, preserving the surrounding room and animation coordinates.

Rebuild its looping GIF from the saved base, without an API call:

```bash
python3 tools/animate_room.py
```

The renderer uses Pillow, a shared palette and nearest-neighbor scaling. It exports `assets/jerry-room-suit.gif` at 960×540, with a still preview in `assets/jerry-room-suit-still.png`. The loop lasts 4.9 seconds, matching the reference's 49 frames at 100 ms per frame. The profile displays it at a maximum width of 420 pixels directly below the introduction; smaller screens scale it to fit. The original room assets remain available in the repository.

## Engineer's mug

`assets/engineer-mug.png` is a cartoon coffee mug made with the imagegen CLI and `gpt-image-2`. Its yellow and red colors match the profile lettering; the inscription reads “Aspiring to be the World’s 2nd Best Engineer.” The compact profile displays it at 150 pixels wide, centered in the footer.

## Research map

`assets/research-map.mmd` is the Mermaid source for `assets/research-map.svg`. The map groups separate ongoing projects by research focus; its lines indicate categories, not runtime data flow or a single deployed architecture. The public summaries describe implementation focus and current evaluation stages while the source repositories remain private.

The SVG was rendered with Mermaid 11.12.1 using plain SVG text labels, a 15px Arial/sans-serif font, 22px node spacing and 30px rank spacing. It is a local, static image and requires no external rendering service when visitors load the profile.
