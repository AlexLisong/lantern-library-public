import os
from pathlib import Path
from PIL import Image
import json
import shutil
import zipfile

ROOT=Path(os.environ['LANTERN_LEGACY_WORKSPACE']).expanduser()
BASE=Path(__file__).resolve().parent
SITE=Path(os.environ['LANTERN_LEGACY_SITE']).expanduser()
OUT=ROOT/'output'
pages=sorted(BASE.glob('final-page-*.png'))
assert len(pages)==12
(SITE/'pages').mkdir(exist_ok=True)
(SITE/'downloads').mkdir(exist_ok=True)
contact=Image.new('RGB',(1440,1440),'#deded6')
for i,p in enumerate(pages):
    im=Image.open(p).convert('RGB');stem='page-'+str(i+1).zfill(2)
    im.save(SITE/'pages'/(stem+'.webp'),quality=90,method=6)
    small=im.copy();small.thumbnail((244,316));small.save(SITE/'pages'/(stem+'-thumb.webp'),quality=83,method=6)
    view=im.copy();view.thumbnail((340,440));contact.paste(view,(10+(i%4)*360,10+(i//4)*478))
contact.save(BASE/'final-contact.png')
pdf=OUT/'pdf/milo-and-the-red-ball.pdf'
shutil.copy2(pdf,SITE/'downloads'/pdf.name)
prompt_files=sorted((ROOT/'tmp/imagegen/milo-red-ball').glob('*.txt'))
prompt_text='MILO AND THE RED BALL - ILLUSTRATION PROMPTS\n\nGenerated with GPT Image 2 via the bundled image-generation CLI and the existing Azure Foundry deployment. Each edited scene uses cover.png as its character/style reference.\n\n'
for prompt in prompt_files:
    prompt_text+='=== '+prompt.stem+' ===\n'+prompt.read_text()+'\n\n'
(OUT/'imagegen/milo-red-ball/illustration-prompts.txt').write_text(prompt_text)
readme='''MILO AND THE RED BALL
An illustrated English story for ages 5-7, beginner level.

Start with the PDF. Meet the friends on page 2; the story is on pages 3-8.
Picture words and activities are on pages 9-11. Page 12 has a grown-up guide and answers.

AUDIO
Read Along.mp3 reads the story and announces page turns.
Listen and Repeat.mp3 practises the words and phrases, leaving time to answer.
Page Audio contains one MP3 for each of the 12 book pages. These clips are used by the ebook. Story page clips also practise the SAY IT line.
All narration was generated locally with Kokoro-82M, voice af_heart, at a gentle 0.86 reading speed. No cloud speech service is used.

EBOOK
Play this page reads the visible page. Turning a page stops the previous audio.
Read to me turns pages when the narration finishes.
Use the arrows, swipe the illustrated page, or open Pages to choose a page.
The current spoken line is highlighted in the large Read along text.
The Slower / Normal / Faster menu changes playback speed without changing pitch.
Use Enlarge for a closer look. On a phone, the large transcript is below the page.
Activities can be answered aloud or on paper; the webpage is a reader, not a drawing app.

ARTWORK
Original AI illustrations generated with GPT Image 2 using the CLI.
The exact prompt set is in Illustration Prompts.txt.
'''
(BASE/'book-pack-readme.txt').write_text(readme)
pack=OUT/'milo-and-the-red-ball-book-pack.zip'
with zipfile.ZipFile(pack,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.write(pdf,pdf.name)
    z.writestr('START HERE.txt',readme)
    z.writestr('Illustration Prompts.txt',prompt_text)
    audio=OUT/'audio/milo-red-ball'
    z.write(audio/'milo-and-the-red-ball-read-along.mp3','Read Along.mp3')
    z.write(audio/'milo-and-the-red-ball-listen-and-repeat.mp3','Listen and Repeat.mp3')
    z.write(audio/'audio-transcript.txt','Audio Transcript.txt')
    for path in sorted((audio/'pages').glob('page-*.mp3')): z.write(path,'Page Audio/'+path.name)
shutil.copy2(pack,SITE/'downloads'/pack.name)
print('Web pages and book pack updated:',pack)
