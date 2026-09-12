import os
from pathlib import Path
import zipfile,shutil

ROOT=Path(os.environ['LANTERN_LEGACY_WORKSPACE']).expanduser()
SITE=Path(os.environ['LANTERN_LEGACY_SITE']).expanduser()
SLUG='the-signal-at-lantern-hill'
out=ROOT/'output'/(SLUG+'-ebook.zip')
files=[SITE/x for x in ['index.html','styles.css','app.js','book-data.js','favicon.svg']]
for directory in ['assets','audio/lantern-hill','pages/lantern-hill']:
    files.extend(p for p in (SITE/directory).rglob('*') if p.is_file())
files.extend([SITE/'downloads'/(SLUG+'.pdf'),SITE/'downloads'/(SLUG+'-book-pack.zip')])
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:
        name=str(p.relative_to(SITE))
        if name=='index.html':
            html=p.read_text().replace('<a href="downloads/the-signal-at-lantern-hill-ebook.zip" download>Save the offline ebook</a>','')
            z.writestr(name,html)
        else:z.write(p,name)
    z.writestr('START HERE.txt','Unzip this entire folder, then open index.html in a modern browser.\nKeep the pages, audio, assets and downloads folders beside index.html.\nEverything needed for reading and listening is included.\n\n'+(Path(__file__).parent/'book-pack-readme.txt').read_text())
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    print('Verified',len(z.namelist()),'files in offline ebook;',round(out.stat().st_size/1024**2,1),'MB.')
shutil.copy2(out,SITE/'downloads'/out.name)
print(out)
