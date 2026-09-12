"""Shared manifest validation; only explicit published books reach the website."""
from pathlib import Path
import json, math, re

ROOT = Path(__file__).resolve().parents[1]

def local_asset(folder, value):
    if not isinstance(value,str) or not value or '\\' in value:
        raise ValueError(f'Invalid asset path: {value!r}')
    p=Path(value)
    if p.is_absolute() or '..' in p.parts or p.parts[0] not in {'pages','audio','downloads','video'}:
        raise ValueError(f'Asset must be in a public book folder: {value}')
    # Public aliases must not expose private source through a file or directory symlink.
    candidate=folder
    if candidate.is_symlink():
        raise ValueError(f'Symlinked book folders are not public assets: {value}')
    for component in p.parts:
        candidate=candidate/component
        if candidate.is_symlink():
            raise ValueError(f'Symlinked paths are not public assets: {value}')
    resolved=candidate.resolve()
    if not resolved.is_relative_to(folder.resolve()) or not resolved.is_file():
        raise ValueError(f'Missing or unsafe asset: {value}')
    if resolved.suffix.lower() not in {'.png','.jpg','.jpeg','.webp','.mp3','.pdf','.mp4','.srt','.vtt','.txt'}:
        raise ValueError(f'Unsupported public asset: {value}')
    return resolved

def validate_book(folder, book):
    slug=book['slug']
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug) or folder.name!=slug:
        raise ValueError('The folder and slug must match and use lowercase words with hyphens')
    for key in ['title','description','audience','level','genre']:
        if not isinstance(book.get(key),str) or not book[key].strip():raise ValueError(f'Missing {key}')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}',book.get('accent','#286567')):raise ValueError('Invalid accent color')
    if not book.get('pages'):raise ValueError('Book has no pages')
    assets={book['cover'],book['pdf']}
    for n,page in enumerate(book['pages'],1):
        if page['number']!=n:raise ValueError('Pages must be numbered consecutively from one')
        for key in ['title','section','note','tip','alt']:
            if not isinstance(page.get(key),str):raise ValueError(f'Page {n}: missing {key}')
        for key in ['image','audio','thumbnail']:assets.add(page[key])
        duration=page['duration']
        if not isinstance(duration,(float,int)) or not math.isfinite(duration) or duration<=0:raise ValueError('Invalid duration')
        if not page.get('cues'):raise ValueError(f'Page {n}: no narration cues')
        previous=0
        for cue in page['cues']:
            if not isinstance(cue.get('text'),str) or not cue['text'].strip():raise ValueError('Empty cue')
            if not previous<=cue['start']<cue['end']<=duration:raise ValueError(f'Page {n}: invalid cue timing')
            previous=cue['end']
    for key in ['storyTrack','practiceTrack']:
        if book.get(key):assets.add(book[key]['file'])
    for key in ['video','subtitles']:
        if book.get(key):assets.add(book[key])
    for value in assets:local_asset(folder,value)
    return assets

def published_books(root=ROOT):
    result=[]
    for path in sorted((root/'books').glob('*/book.json')):
        book=json.loads(path.read_text())
        if book.get('status')!='published':continue
        validate_book(path.parent,book)
        result.append((path.parent,book))
    return result
