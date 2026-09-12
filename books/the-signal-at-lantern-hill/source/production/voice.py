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
OUT = BASE.parents[2] / 'output' / 'audio' / 'lantern-hill'
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
            '-codec:a', 'libmp3lame', '-b:a', '96k', '-id3v2_version', '3',
            '-metadata', 'title=' + (title or (BOOK['title'] + (' - Read Along' if 'read-along' in name else ' - Listen and Repeat'))),
            '-metadata', 'artist=Kokoro af_heart', str(mp3)
        ], check=True)
        return {'file': str(mp3), 'duration': round(len(data) / RATE, 3), 'cues': self.cues}


