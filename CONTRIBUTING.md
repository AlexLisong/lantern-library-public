# Contributing to Lantern Library

Contributions to the reader, publishing tools, and documentation are welcome.
Please read the [README](README.md), [content rights](docs/PROVENANCE.md), and
[code of conduct](CODE_OF_CONDUCT.md) first.

## Pick a focused change

For a bug, include the book/page, browser or command, expected behavior, and a
minimal reproduction. For a new feature or a full book, discuss scope in an issue
first. Accessibility, readable error messages, documentation, and small editorial
corrections are useful entry points. Maintainers review scope and correctness;
there is no guaranteed response schedule.

Fork the repository, create a descriptive branch, and follow the README setup.
No cloud account or deployment access is needed. Keep existing Python and browser
JavaScript patterns; avoid adding a framework for a small reader improvement.

## Verify your change

```sh
npm test
npm run build
npm run dev
```

The tests exercise manifest validation, asset traversal and symlink rejection,
draft exclusion, and offline packages. Add a focused regression test when fixing
a bug in these behaviors. For reader changes, inspect desktop and phone widths;
check keyboard navigation, page selection, playback, seek/speed controls,
auto-next stops, and downloads. Include the checks and outcomes in your PR.

For a book change, inspect every rendered page for layout and read the matching
audio transcript. Listen to changed narration and regenerate audio cues/video
when timing changes. Follow [the creation workflow](docs/creating-books.md).
Avoid committing generated caches, models, temporary WAVs, or build output.

## Submit

Keep the PR small, explain the problem and behavior, link the relevant issue,
and document any limitations. Include screenshots for visible changes using only
public sample content. Do not include local paths, hostnames, accounts, secrets,
or private learner data in examples or logs.

Code and technical documentation contributions are submitted under the project
MIT license. For books, artwork, recordings, fonts, or other media, state the
creator, source, and explicit redistribution terms; do not assume the code
license covers them. Do not contribute material you cannot authorize us to share.
