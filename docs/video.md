# Ebook to video

The initial export is a **16:9, 1920×1080 narrated comic video** suitable for a
normal YouTube upload and other landscape video platforms. It uses the original
panels, chapter titles, sentence captions and the existing Kokoro soundtrack.
There is no added music. The separate UTF-8 SRT can be uploaded as a subtitle track.

```sh
python3 scripts/export_video.py the-signal-at-lantern-hill
```

Requires Pillow and ffmpeg with libx264. macOS users can optionally use
`--encoder h264_videotoolbox` for faster hardware encoding, but its constant
bitrate produces a much larger file. The default libx264 export compresses still
comic panels more efficiently.

## Timing format

`book.json` contains `storyTrack.file`, its duration, and sentence cues with
`start`, `end`, `text` and optional page numbers. Generate this from current page
audio with `scripts/assemble_story.py`. The initial edition retains its original
continuous read-along track, including spoken page-turn prompts.

`source/video-scenes.json` is an ordered list:

```json
[
  {"start": 0, "image": "source/illustrations/cover.png", "title": "An illustrated mystery", "cover": true},
  {"start": 12.5, "image": "source/illustrations/page-03.png", "crop": [0, 0, 1536, 500], "title": "Chapter 1"}
]
```

Times are seconds into the soundtrack. A scene remains until the next scene's
start. Captions follow sentence cue timings. Use `"fit": "contain"` for complete
portrait pages; original comic panels fill the landscape area more naturally.
Review a few frames around each scene change and listen before uploading.

## Publishing the video

Upload the MP4 to YouTube Studio or your chosen platform. Add a title, description,
thumbnail and the SRT subtitle file, then review the platform's audience settings.
For a children's story, assess the platform's “made for kids” criteria honestly.
The audience setting is a publisher decision; an English-learning label alone
does not decide it. This repository does not upload to any social account.

For Shorts/Reels/TikTok, make a separate **9:16** edit using a short scene or
chapter, with larger captions and a reframed panel. Avoid squeezing the entire
landscape page into a vertical frame. Vertical export and social upload are not
implemented in this version.
