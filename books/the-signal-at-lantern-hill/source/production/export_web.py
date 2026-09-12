import os
from pathlib import Path
from PIL import Image
import json, shutil, zipfile

ROOT=Path(os.environ['LANTERN_LEGACY_WORKSPACE']).expanduser()
BASE=Path(__file__).resolve().parent
SITE=Path(os.environ['LANTERN_LEGACY_SITE']).expanduser()
OUT=ROOT/'output'
SLUG='the-signal-at-lantern-hill'
pages=sorted(BASE.glob('final-page-*.png'))
assert len(pages)==16
for folder in ['pages/lantern-hill','audio/lantern-hill','downloads']:
    (SITE/folder).mkdir(parents=True,exist_ok=True)
contact=Image.new('RGB',(1600,2120),'#d8dddc')
for i,p in enumerate(pages):
    im=Image.open(p).convert('RGB');stem='page-'+str(i+1).zfill(2)
    im.save(SITE/'pages/lantern-hill'/(stem+'.webp'),quality=92,method=6)
    small=im.copy();small.thumbnail((244,316));small.save(SITE/'pages/lantern-hill'/(stem+'-thumb.webp'),quality=85,method=6)
    view=im.copy();view.thumbnail((380,492));contact.paste(view,(10+(i%4)*400,10+(i//4)*530))
contact.save(BASE/'final-contact.jpg',quality=92)
audio=OUT/'audio/lantern-hill'
for p in (audio/'pages').glob('page-*.mp3'):shutil.copy2(p,SITE/'audio/lantern-hill'/p.name)
data=json.loads((BASE/'page-audio-metadata.json').read_text())
data.pop('storyTrack',None);data.pop('practiceTrack',None)
(SITE/'book-data.js').write_text('window.BOOK = '+json.dumps(data,ensure_ascii=False,indent=2)+';\n')
pdf=OUT/'pdf'/(SLUG+'.pdf')
shutil.copy2(pdf,SITE/'downloads'/pdf.name)
prompt_text='THE SIGNAL AT LANTERN HILL - ILLUSTRATION PROMPTS\n\nOriginal AI illustrations generated with GPT Image 2 through the bundled image-generation CLI using Azure Foundry. The cover is the style and character reference; chapters 7 and 8 also use chapter 3 for Mr Reed.\n\n'
for p in sorted((ROOT/'tmp/imagegen/lantern-hill').glob('*.txt')):
    prompt_text+='=== '+p.stem+' ===\n'+p.read_text()+'\n\n'
(OUT/'imagegen/lantern-hill/illustration-prompts.txt').write_text(prompt_text)
readme='''THE SIGNAL AT LANTERN HILL
A mystery in eight chapters. Ages 10-12, intermediate English.

THE BOOK
The PDF has 16 pages. Meet the investigators on page 2; read the eight
illustrated chapters on pages 3-10. Vocabulary and activities are on
pages 11-14; suggested answers on page 15; a teaching guide on page 16.

AUDIO
There is a separate MP3 for every page, plus a continuous story track
and vocabulary practice. All speech was generated locally using
Kokoro-82M, voice af_heart, at 0.96 speed. No cloud speech service was used.

EBOOK
Open index.html in a modern browser after unzipping the ebook download.
Play this page reads the visible page. Turning manually stops the old audio.
Read to me advances after narration ends and stops after page 10
(the story) and page 14 (before suggested answers).
Use arrows, swipe the picture, or select Pages. Enlarge gives a closer view.
Sentence highlighting, replay, a seek slider, and speed controls support listening.
Activities can be answered aloud or on paper.

ARTWORK
Original AI illustrations generated with GPT Image 2 using the CLI.
The exact prompts are included in Illustration Prompts.txt.
The story, village, characters, and history are fictional.
'''
(BASE/'book-pack-readme.txt').write_text(readme)
pack=OUT/(SLUG+'-book-pack.zip')
with zipfile.ZipFile(pack,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.write(pdf,pdf.name);z.writestr('START HERE.txt',readme);z.writestr('Illustration Prompts.txt',prompt_text)
    z.write(audio/(SLUG+'-story.mp3'),'Complete Story.mp3')
    z.write(audio/(SLUG+'-vocabulary.mp3'),'Vocabulary Practice.mp3')
    z.write(audio/'audio-transcript.txt','Audio Transcript.txt')
    for p in sorted((audio/'pages').glob('page-*.mp3')):z.write(p,'Page Audio/'+p.name)
shutil.copy2(pack,SITE/'downloads'/pack.name)
print('Exported all 16 illustrated pages, narration, metadata, PDF, and book pack.')
