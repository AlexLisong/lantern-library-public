# Creating another ebook

## 1. Start an unpublished draft

Run `python3 scripts/new_book.py your-slug --title "Your Book Title"`.
Set the audience, English level, genre, description and voice in `book.json`.
Drafts stay out of the website; committed drafts remain visible in the repository. The default audience is ages 10–12, intermediate.

## 2. Write and illustrate

Edit `source/manuscript.json`. Supported layouts are `cover`, `story` (two panels),
and `lesson` (paragraphs). Each story page has a title, two narrative paragraphs,
an illustration filename, and an optional question. Add vocabulary, comprehension,
language practice, writing and suggested answers as lesson pages. Put
`"autoNext": false` at the story ending and before the answer key.

Keep the story appropriate for the selected age and level. Introduce useful words
in context, let readers infer from evidence, and check the answers against the text.

Generate original illustrations with your configured image-generation CLI. Keep
the exact prompts under `source/prompts/` and original PNGs under
`source/illustrations/`. Use a consistent character reference, clothing, palette
and setting. A two-panel 1536×1024 image works well; specify `crops.top` and
`crops.bottom` as `[left, top, right, bottom]` to remove its gutter. Never store
API keys in prompts, source or book metadata.

## 3. Render the PDF and page images

Install `requirements.txt` in your chosen Python environment and install Poppler
(`pdftoppm`) and ffmpeg. Then run:

```sh
python3 scripts/render_pdf.py your-slug
```

This fills `book.json` with page metadata and narration text. It deliberately
fails on overflowing paragraphs: shorten them or split the page. Inspect **every
PDF page** for clipping, correct artwork crops, readable text and matching clues.
Render again after edits; page audio must then be regenerated because the text
may have changed.

Lantern Hill's original custom 16-page layout and its first-edition source are
preserved under `source/production/`. Its `build_book.py` resolves this repository's paths and can regenerate the original PDF (macOS fonts or Linux DejaVu fonts). That layout is specific to this
book. The root `scripts/` workflow is the reusable pipeline for future books;
archived export scripts are provenance rather than required build dependencies.

## 4. Generate local speech

Use your existing Kokoro environment, or install `requirements-audio.txt` and
download `hexgrad/Kokoro-82M` and the selected voice once. Generation runs in
offline mode and fails if the model is not cached. English text processing may
also need the model's normal local dependencies, including espeak-ng.

```sh
/path/to/kokoro/python scripts/render_audio.py your-slug --voice af_heart
```

The script uses each page's `narration` array, generates one MP3 per page, records
exact sentence start/end times, and keeps a local sentence cache under `.build/`.
`pause` values are seconds after each sentence. Default narration speed is 0.96.
The reader can independently slow or speed playback while preserving pitch.
Changing page speech invalidates references to old companion audio and videos;
use the next step to regenerate them.

## 5. Optional video and continuous story

```sh
python3 scripts/assemble_story.py your-slug
python3 scripts/export_video.py your-slug
```

Only pages with sections starting `CHAPTER` enter the continuous story.
The default scene list shows each rendered page in a landscape frame. For a
comic-panel video like Lantern Hill, edit `source/video-scenes.json` to select
original illustrations, crop boxes and audio-aligned scene start times.
See [video.md](video.md).

## 6. Publish and verify

Set `status` to `published` in `book.json`, then run `npm test` and `npm run build`.
Missing files, unsafe asset paths, page numbering errors and invalid cue timings
stop the build. It regenerates the library, each book route, the book/audio ZIP
and the offline ebook ZIP. A book can be removed by setting it back to `draft`
and deploying a rebuilt release.

Check the reader in a browser: images, page chooser, enlargement, matching audio,
seek, speed, auto-next, planned stops, downloads, and a narrow phone viewport.
Review the audio itself, especially names and numbers. Keep original source
and finished assets in Git; exclude temporary WAVs, model weights and caches.
