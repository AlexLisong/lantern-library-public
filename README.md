# Lantern Library

A static illustrated ebook library with synchronized page narration, printable
learning material, offline reading packs, and narrated video exports. It includes
**The Signal at Lantern Hill**, an English-learning mystery for ages 10–12.

The shared reader and publishing tools are MIT licensed. Book media have separate
rights; see [content and third-party notices](docs/PROVENANCE.md).

## Quick start

Install **Python 3.12+** and **Node.js 22** (`.nvmrc` pins the tested version).
Reading and building the included book requires no npm packages, Python packages,
model downloads, API keys, or database.

```sh
git clone https://github.com/AlexLisong/lantern-library-public.git
cd lantern-library-public
npm test
npm run build
npm run dev
```

Open **http://localhost:8766**. The repository includes finished book assets, so
cloning can take longer than a code-only project. `npm run build` creates `dist/`;
the development server serves that output. Rebuild after editing source files.

## What works today

- Search and filter the catalog by age and reading level.
- Read illustrated pages with narration, sentence cues, playback speed controls,
  and automatic page turning.
- Download PDFs, book/audio bundles, and a self-contained offline ebook.
- Scaffold a book and optionally generate PDFs, local speech, and captioned video.

This is an early project with one published book. Content creation requires
editorial, visual, and audio review. There is no account system, online editor,
cloud speech API, or automated social upload.

## Create a book

```sh
npm run new-book -- forest-mystery --title "The Forest Mystery"
```

Write the manuscript, add appropriately licensed illustrations, render and inspect
the pages, generate narration, and set the manifest to `published` when ready.
The [creation guide](docs/creating-books.md) covers optional Python dependencies,
Poppler, ffmpeg, and offline Kokoro setup. See [video exports](docs/video.md) for
captions and scene timing.

A draft is excluded from the built website; **anything committed to a public
repository is still public**, including draft stories and prompts.

## How it fits together

| Path | Purpose |
| --- | --- |
| `books/<slug>/book.json` | Catalog metadata, pages, narration cues, publication status |
| `books/<slug>/{pages,audio,downloads,video}` | Finished assets used by the reader |
| `books/<slug>/source` | Manuscripts, illustration prompts, original artwork and production sources |
| `web/reader` | Shared page reader and playback controls |
| `web` | Catalog page, styles, and filtering |
| `scripts` | Validation, scaffolding, build and media tools |
| `tests` | Manifest, path safety and offline bundle regression tests |
| `archive` | Superseded public reference material, excluded from the website |

The build validates published manifests, copies only their allowlisted assets,
generates book routes and offline packs, and writes a checksum manifest. Any
static host can serve `dist/`. Optional [deployment examples](docs/aws.md) use
operator-supplied configuration and are not needed for local development.

## Contribute

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Useful first changes include clearer
reader controls, keyboard accessibility, manifest validation, and editorial
corrections with page references. Discuss large changes before implementing them.
Follow the [code of conduct](CODE_OF_CONDUCT.md) and report vulnerabilities through
[SECURITY.md](SECURITY.md).
