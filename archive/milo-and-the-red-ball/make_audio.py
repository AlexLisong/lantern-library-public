"""Render the book locally with the user's installed Kokoro model."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

import numpy as np
import soundfile as sf
from kokoro import KPipeline

BASE = Path(__file__).resolve().parent
OUT = BASE.parents[2] / 'output' / 'audio' / 'milo-red-ball'
OUT.mkdir(parents=True, exist_ok=True)
CACHE = BASE / 'speech-cache'
CACHE.mkdir(exist_ok=True)
BOOK = json.loads((BASE / 'book.json').read_text())
RATE = 24000
VOICE = BOOK['voice']
SPEED = BOOK['speed']
pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M', device='cpu')


def speak(text):
    key = hashlib.sha256((VOICE + str(SPEED) + text).encode()).hexdigest()[:20]
    path = CACHE / (key + '.wav')
    if path.exists():
        data, rate = sf.read(path, dtype='float32')
        assert rate == RATE
        return data
    chunks = []
    for result in pipeline(text, voice=VOICE, speed=SPEED):
        a = result.audio
        if a is not None:
            chunks.append(np.asarray(a, dtype=np.float32))
    if not chunks:
        raise RuntimeError('No audio for: ' + text)
    data = np.concatenate(chunks)
    assert np.isfinite(data).all() and np.max(np.abs(data)) > 0.001
    sf.write(path, data, RATE, subtype='PCM_16')
    print('Spoken:', text, flush=True)
    return data


class Track:
    def __init__(self):
        self.parts = []
        self.samples = 0
        self.cues = []

    def silence(self, seconds):
        part = np.zeros(round(seconds * RATE), dtype=np.float32)
        self.parts.append(part)
        self.samples += len(part)

    def line(self, text, pause=0.65, page=None):
        start = self.samples / RATE
        part = speak(text)
        self.parts.append(part)
        self.samples += len(part)
        self.cues.append({'start': round(start, 3), 'end': round(self.samples / RATE, 3), 'text': text, 'page': page})
        self.silence(pause)

    def save(self, name, title=None):
        data = np.concatenate(self.parts)
        peak = float(np.max(np.abs(data)))
        if peak > 0.93:
            data *= 0.93 / peak
        wav = BASE / (name + '.wav')
        wav.parent.mkdir(parents=True, exist_ok=True)
        sf.write(wav, data, RATE, subtype='PCM_16')
        mp3 = OUT / (name + '.mp3')
        mp3.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav),
            '-af', 'loudnorm=I=-18:TP=-1.5:LRA=7', '-ar', str(RATE), '-ac', '1',
            '-codec:a', 'libmp3lame', '-b:a', '128k', '-id3v2_version', '3',
            '-metadata', 'title=' + (title or (BOOK['title'] + (' - Read Along' if 'read-along' in name else ' - Listen and Repeat'))),
            '-metadata', 'artist=Kokoro af_heart', str(mp3)
        ], check=True)
        return {'file': str(mp3), 'duration': round(len(data) / RATE, 3), 'cues': self.cues}


def build_download_tracks():
    story = Track()
    story.silence(0.5)
    story.line(BOOK['title'] + '.', pause=1)
    story.line('A story to read together.', pause=1)
    story.line('Open your book to page three. Listen and look at the pictures.', pause=2)
    page_starts = {}
    page_names = {3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight'}
    for item in BOOK['story']:
        page = item['page']
        page_starts[str(page)] = round(story.samples / RATE, 3)
        heading = item['title'] if item['title'].endswith(('.', '!', '?')) else item['title'] + '.'
        story.line('Page ' + page_names[page] + '. ' + heading, pause=0.9, page=page)
        for panel in item['panels']:
            if panel['caption']:
                story.line(panel['caption'], page=page)
            for speech in panel['speech']:
                story.line(speech, pause=0.8, page=page)
            story.silence(0.5)
        if page != 8:
            story.line('Turn the page.', pause=2, page=page)
    story.line('The end.', pause=1.5, page=8)
    story_result = story.save('milo-and-the-red-ball-read-along')
    story_result['page_starts'] = page_starts
    print('Story complete:', story_result['duration'], 'seconds', flush=True)
    
    practice = Track()
    practice.silence(0.5)
    practice.line('Milo and the Red Ball. Listen and repeat.', pause=1)
    practice.line('Look at page nine. Listen, point, and say each word.', pause=2)
    for word in BOOK['words']:
        practice.line(word + '.', pause=1)
        practice.line('Your turn.', pause=3.5)
        practice.line(word + '.', pause=1.2)
    practice.line('Now look at page ten. Listen and say the phrases.', pause=2)
    for phrase in BOOK['phrases'][:3]:
        practice.line(phrase.capitalize() + '.', pause=1)
        practice.line('Your turn.', pause=4)
        practice.line(phrase.capitalize() + '.', pause=1.2)
    practice.line('Now let us talk like Milo and Pip.', pause=1.5)
    for phrase in BOOK['phrases'][3:]:
        practice.line(phrase, pause=1)
        practice.line('Your turn.', pause=4)
        practice.line(phrase, pause=1.2)
    practice.line('Well done! You can read and speak English with Milo and Pip.', pause=1.5)
    practice_result = practice.save('milo-and-the-red-ball-listen-and-repeat')
    metadata = {'engine': 'Kokoro-82M (local)', 'voice': VOICE, 'speed': SPEED, 'sample_rate': RATE, 'story': story_result, 'practice': practice_result}
    (BASE / 'audio-metadata.json').write_text(json.dumps(metadata, indent=2))
    (OUT / 'audio-transcript.txt').write_text(
        BOOK['title'] + '\nREAD ALONG\n\n' + '\n'.join(x['text'] for x in story.cues)
        + '\n\nLISTEN AND REPEAT\n\n' + '\n'.join(x['text'] for x in practice.cues) + '\n'
    )
    print(json.dumps({'story_seconds': story_result['duration'], 'practice_seconds': practice_result['duration'], 'output': str(OUT)}), flush=True)


if __name__ == "__main__":
    build_download_tracks()
