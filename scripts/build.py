"""Build a complete static library and standalone ebook archives. No dependencies."""
from pathlib import Path
import hashlib, html, json, shutil, tempfile, zipfile
from catalog import ROOT, published_books, validate_book

def esc(value):return html.escape(str(value),quote=True)

def reader_html(book,offline=False):
    source=(ROOT/'web/reader/index.html').read_text()
    values={'TITLE':book['title'],'UPPER_TITLE':book['title'].upper(),'SLUG':book['slug'],
        'AUDIENCE':book['audience'],'DESCRIPTION':book['description'],'PAGE_COUNT':len(book['pages']),'PDF':book['pdf']}
    for key,value in values.items():source=source.replace('__'+key+'__',esc(value))
    video=f'<a href="{esc(book["video"])}" download>Download story video</a>' if book.get('video') and not offline else ''
    source=source.replace('__VIDEO_LINK__',video)
    if offline:
        source=source.replace('../../assets/','assets/').replace('href="../../"','href="#page-1"').replace('Back to Lantern Library','Go to the cover')
        source=source.replace(f'<a href="downloads/{book["slug"]}-ebook.zip" download>Save the offline ebook</a>','')
    return source

def public_data(book):
    keys=['schemaVersion','title','slug','audience','voice','pages']
    data={key:book[key] for key in keys if key in book}
    data['pages']=[{k:v for k,v in p.items() if k!='narration'} for p in book['pages']]
    return 'window.BOOK = '+json.dumps(data,ensure_ascii=False)+';\n'

def build(root=ROOT):
    books=published_books(root)
    if not books:raise ValueError('No published books; complete a draft before publishing it')
    output=root/'dist'
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError('Build output must be a regular dist directory')
    staging=root/'.build';staging.mkdir(exist_ok=True)
    if staging.is_symlink():raise ValueError('Build staging must not be a symlink')
    with tempfile.TemporaryDirectory(prefix='static-',dir=staging) as work:
        dist=Path(work)/'dist'
        count=_render(root,dist,books)
        previous=Path(work)/'previous'
        if output.exists():output.rename(previous)
        try:dist.rename(output)
        except BaseException:
            if previous.exists():previous.rename(output)
            raise
    print(f'Built {len(books)} book(s), {count} files. Static output: {output}')

def _render(root,dist,books):
    dist.mkdir()
    assets=dist/'assets';assets.mkdir()
    for p in (root/'web/assets').iterdir():
        if p.is_file():shutil.copy2(p,assets/p.name)
    for source,name in [('reader/styles.css','reader.css'),('reader/app.js','reader.js'),('library.css','library.css'),('library.js','library.js'),('favicon.svg','favicon.svg')]:
        shutil.copy2(root/'web'/source,assets/name)
    cards=[]
    for folder,book in books:
        slug=book['slug'];dest=dist/'books'/slug;dest.mkdir(parents=True)
        allowed=validate_book(folder,book)
        # Public files are an explicit allowlist, never a recursive source-folder copy.
        for value in allowed:
            target=dest/value;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(folder/value,target)
        (dest/'index.html').write_text(reader_html(book))
        (dest/'book-data.js').write_text(public_data(book))
        readme=f'{book["title"]}\n{book["audience"]}\n\nUnzip the entire folder, then open index.html in a modern browser.\nEach page has its own narration. Manual turns stop old audio. Read to me turns pages automatically and respects the book\'s planned pauses.\n\nPDF and individual MP3 files are included. Activities can be answered on paper or aloud.\n'
        pack=dest/'downloads'/(slug+'-book-pack.zip')
        with zipfile.ZipFile(pack,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('START HERE.txt',readme)
            for value in sorted(allowed):
                if Path(value).suffix in {'.pdf','.mp3','.srt','.vtt'}:z.write(folder/value,value)
        offline=dest/'downloads'/(slug+'-ebook.zip')
        with zipfile.ZipFile(offline,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('START HERE.txt',readme);z.writestr('index.html',reader_html(book,True));z.writestr('book-data.js',public_data(book))
            for p in assets.iterdir():
                if p.is_file() and not p.name.startswith('library'):z.write(p,'assets/'+p.name)
            for value in sorted(allowed):
                if Path(value).suffix!='.mp4':z.write(folder/value,value)
            z.write(pack,'downloads/'+pack.name)
        minutes=round(sum(p['duration'] for p in book['pages'] if p['section'].startswith('CHAPTER'))/60)
        cards.append(f'''<article class="book-card" data-search="{esc(' '.join([book['title'],book['description'],book['level'],book['genre']]).lower())}" data-level="{esc(book['level'])}">
<a class="cover-link" href="books/{slug}/" aria-label="Read {esc(book['title'])}"><img src="books/{slug}/{esc(book['cover'])}" alt="{esc(book['title'])} book cover" width="612" height="792"></a>
<div class="book-info"><span class="book-genre">{esc(book['genre'])} · Illustrated adventure</span><h2><a href="books/{slug}/">{esc(book['title'])}</a></h2><p>{esc(book['description'])}</p><div class="book-meta"><span>Ages {book['ageMin']}–{book['ageMax']}</span><span>{esc(book['level'])} English</span><span>{len(book['pages'])} pages</span><span>{minutes} min story</span></div><div class="book-actions"><a class="primary" href="books/{slug}/">Open the book <span aria-hidden="true">→</span></a><a class="quiet" href="books/{slug}/{esc(book['pdf'])}" download>Download PDF</a></div><div class="included">Page-by-page audio <span>·</span> Vocabulary & activities <span>·</span> Offline edition</div>{f'<a class="video-link" href="books/{slug}/{esc(book["video"])}" download>↓ Download the narrated video</a>' if book.get('video') else ''}</div></article>''')
    template=(root/'web/index.html').read_text().replace('__BOOKS__','\n'.join(cards)).replace('__COUNT__',str(len(cards)))
    levels=sorted(set(book['level'] for _,book in books))
    template=template.replace('__LEVELS__',''.join(f'<option>{esc(x)}</option>' for x in levels))
    (dist/'index.html').write_text(template)
    (dist/'404.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Page not found · Lantern Library</title><h1>That page is not in the library.</h1><p><a href="/">Return to Lantern Library</a></p></html>')
    (dist/'robots.txt').write_text('User-agent: *\nAllow: /\n')
    manifest={str(p.relative_to(dist)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dist.rglob('*')) if p.is_file() and p.name!='checksums.json'}
    (dist/'checksums.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return len(manifest)

if __name__=='__main__':build()
