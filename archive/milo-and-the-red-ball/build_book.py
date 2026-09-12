"""Create a twelve-page illustrated English reader with selectable text."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageOps
from art import Art, INK, CREAM, PAPER, TEAL, MINT, SKY, RED, YELLOW, PEACH, MUTED

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
OUT = ROOT / 'output' / 'pdf' / 'milo-and-the-red-ball.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
BOOK = json.loads((BASE / 'book.json').read_text())
META = json.loads((BASE / 'audio-metadata.json').read_text())
IMAGES = ROOT / 'output' / 'imagegen' / 'milo-red-ball'
READY = BASE / 'print-images'
READY.mkdir(exist_ok=True)
W, H = 612, 792
c = canvas.Canvas(str(OUT), pagesize=(W,H), pageCompression=1)
c.setTitle(BOOK['title'] + ' - A Beginner English Cartoon Story')
c.setAuthor('Original story and illustrations created for English learners')
c.setSubject('Ages 5-7. Friendship, picture vocabulary, and under / in / behind.')
c.setCreator('ReportLab - original vector artwork; companion narration by local Kokoro')
a = Art(c)


def start(page, section='STORY TIME', title=None, subtitle=None):
    c.saveState()
    c.translate(0,H)
    c.scale(1,-1)
    a.rect(0,0,W,H,PAPER)
    if page>1:
        a.text('LITTLE ENGLISH',36,27,10,'Round',TEAL)
        a.text(section,576,27,9,'BodyBold',MUTED,align='right')
        if title: a.text(title,36,66,32,'Round')
        if subtitle: a.text(subtitle,37,108,14,'Body',MUTED)
    a.line(36,750,576,750,'#DCE5D9',1)
    if page>1: a.text('Milo and the Red Ball',36,763,9,'Body',MUTED)
    a.oval(550,757,26,26,TEAL)
    a.text(str(page),563,764,11,'Round','#FFFFFF',align='center')


def end():
    c.restoreState()
    c.showPage()


def pill(label,x,y,w,fill=TEAL,textcolor='#FFFFFF'):
    a.rect(x,y,w,27,fill,r=13)
    a.text(label,x+w/2,y+7,10,'Round',textcolor,align='center')


def circnum(n,x,y,fill=TEAL,r=12):
    a.oval(x-r,y-r,2*r,2*r,fill)
    a.text(str(n),x,y-5.5,12,'Round','#FFFFFF',align='center')


def clipped_scene(x,y,w,h,draw,r=19):
    c.saveState()
    p=c.beginPath(); p.roundRect(x,y,w,h,r)
    c.clipPath(p,stroke=0,fill=0)
    with a.at(x,y): draw()
    c.restoreState()


def picture(path,x,y,w,h,crop=None,contain=False):
    """Embed a carefully fitted print image with the correct top-down orientation."""
    path=Path(path)
    im=Image.open(path).convert('RGB')
    if crop: im=im.crop(crop)
    target=(round(w*3),round(h*3))
    im=ImageOps.pad(im,target,method=Image.Resampling.LANCZOS,color=im.getpixel((0,0))) if contain else ImageOps.fit(im,target,method=Image.Resampling.LANCZOS)
    suffix=('-'+'-'.join(map(str,crop))) if crop else ''
    cache=READY/(path.stem+suffix+'-'+str(target[0])+'x'+str(target[1])+'.jpg')
    im.save(cache,quality=94,subsampling=0)
    c.saveState()
    c.translate(x,y+h)
    c.scale(1,-1)
    c.drawImage(str(cache),0,0,w,h)
    c.restoreState()


SPEECH = {
    'friends':[(24,7,214,45,'Hello, Pip!',(164,92),20),(305,7,207,45,"Let's play!",(388,110),20)],
    'gone':[(210,6,305,67,['Oh, no!','Where is my ball?'],(157,107),20)],
    'tree_question':[(24,6,306,46,'Is it under the tree?',(147,107),19)],
    'leaf':[(185,6,258,46,'No. It is a leaf!',(252,109),20)],
    'box_question':[(24,6,270,46,'Is it in the box?',(141,108),20)],
    'hat':[(206,6,270,46,'No. It is a hat!',(279,113),20)],
    'bench_question':[(23,6,317,46,'Look behind the bench!',(263,107),18.5)],
    'found':[(185,6,252,46,'My red ball!',(359,103),21)],
    'thanks':[(19,6,256,46,'Thank you, Pip!',(162,99),19),(295,6,225,46,"You're welcome!",(402,110),18.5)],
    'play':[(204,6,207,46,"Let's play!",(171,102),21)]
}


def ai_scene(name,w,h):
    for page in BOOK['story']:
        for index,panel in enumerate(page['panels']):
            if panel['scene']==name:
                image=IMAGES/('page-'+str(page['page']).zfill(2)+'.png')
                crop=(0,0,1536,556) if index==0 else (0,592,1536,1152)
                speech=SPEECH.get(name,[])
                top=47 if speech else 0
                if speech: a.rect(0,0,w,top,'#F8EDD5')
                picture(image,0,top,w,h-top,crop)
                for bubble in speech:
                    x,y,bw,bh,words,tail,size=bubble
                    if name=='gone': x,bw,words=98,405,'Oh, no! Where is my ball?'
                    a.bubble(x,3,bw,37,words,(tail[0],54),min(size,19))
                return
    raise ValueError(name)


def scene_panel(panel,x,y,w,h,number):
    # Scale the wide vector stage consistently and keep captions outside it.
    has_caption = bool(panel['caption'])
    art_h = h-36 if has_caption else h
    def draw():
        ai_scene(panel['scene'],w,art_h)
        if has_caption:
            a.rect(0,art_h,w,36,'#FFFFFF')
            a.line(0,art_h,w,art_h,'#D4DFD4',1)
            size=20
            while pdfmetrics.stringWidth(panel['caption'],'Body',size)>w-38: size-=0.25
            a.text(panel['caption'],19,art_h+8,size,'Body')
    clipped_scene(x,y,w,h,draw)
    a.rect(x,y,w,h,None,'#B7CFC7',r=19,sw=1.2)
    # Panel order is shown outside the artwork so it never covers a character.
    a.oval(x-12,y+14,24,24,TEAL,PAPER,2)
    a.text(str(number),x,y+20,11,'Round','#FFFFFF',align='center')


def word_art(name,x,y,scale=1):
    index=BOOK['words'].index(name)
    row,col=divmod(index,3)
    crop=(col*512,row*512,(col+1)*512,(row+1)*512)
    picture(IMAGES/'picture-words.png',x,y,142*scale,142*scale,crop)


def stamp_time(seconds):
    seconds=int(seconds)
    return f'{seconds//60}:{seconds%60:02d}'


# 1. Cover.
start(1)
pill('A LITTLE ENGLISH STORY',36,34,196)
a.text('Milo and the',36,86,42,'Round')
a.text('Red Ball',33,135,70,'Round',RED)
a.text(BOOK['subtitle'],39,219,17,'Body',MUTED)

def cover_art():
    picture(IMAGES/'cover.png',0,0,564,352)
clipped_scene(24,275,564,352,cover_art,r=26)
a.text('Read. Look. Say.',306,651,24,'Round',TEAL,align='center')
a.text('Ages 5-7  /  Beginner English',306,689,14,'BodyBold',MUTED,align='center')
a.text('Story + picture words + activities + read-aloud audio',306,714,12,'Body',MUTED,align='center')
end()

# 2. The cast and a child-facing introduction.
start(2,'MEET THE FRIENDS','Hello, friends!','Point to Milo. Point to Pip. Say hello!')
a.rect(36,147,258,325,'#FBEDC6',r=23)
a.rect(310,147,266,325,'#FBEDC6',r=23)
clipped_scene(46,199,238,227,lambda:picture(IMAGES/'characters.png',0,0,238,227,(0,0,768,1024),contain=True),r=12)
clipped_scene(320,199,246,227,lambda:picture(IMAGES/'characters.png',0,0,246,227,(768,0,1536,1024),contain=True),r=12)
a.bubble(78,158,171,37,'Hello!',(169,207),20)
a.bubble(349,158,177,37,'Hi!',(437,207),20)
a.text('Milo',165,435,27,'Round',align='center')
a.text('Pip',443,435,27,'Round',align='center')
a.text('Milo is a rabbit.',165,482,18,'Body',align='center')
a.text('Pip is a bird.',443,482,18,'Body',align='center')
a.rect(36,529,540,188,'#F1F3E6',r=22)
a.text('Ready to read?',57,549,24,'Round',TEAL)
for n,(yy,txt) in enumerate([(589,'Look at the pictures.'),(627,'Listen to the story.'),(665,'Read and say the words.')],1):
    circnum(n,71,yy+10,r=11)
    a.text(txt,95,yy,18,'Body')
end()

# 3-8. Six two-panel comic pages. Every caption and balloon is in the audio.
for page in BOOK['story']:
    start(page['page'],'READ THE STORY',page['title'])
    scene_panel(page['panels'][0],36,109,540,274,1)
    scene_panel(page['panels'][1],36,398,540,274,2)
    a.rect(36,687,540,44,'#E6EFE3',r=14)
    a.text('SAY IT',55,703,10,'Round',TEAL)
    a.text(page['say'],133,698,21,'Round')
    end()

# 9. Picture vocabulary with six large, separate visual anchors.
start(9,'LOOK AND SAY','Picture words','Listen to the practice audio. Point and say each word.')
for i,name in enumerate(BOOK['words']):
    row,col=divmod(i,3)
    x=36+col*184; y=153+row*220
    a.rect(x,y,172,201,'#F7F0DF',r=20)
    clipped_scene(x+7,y+5,158,146,lambda name=name:word_art(name,8,2,1),r=15)
    a.text(name,x+86,y+158,27,'Round',align='center')
a.rect(36,615,540,109,'#FFF0D3',r=20)
a.text('Can you find it?',56,633,22,'Round')
a.text('Find a red leaf in the story.',56,669,18,'Body')
a.text('Find a red hat. Find the red ball!',56,696,18,'Body')
end()

# 10. A clearly illustrated preposition task with exactly one answer per row.
start(10,'PLAY WITH WORDS','Where is the ball?','Look at each picture. Circle the correct word.')
for i in range(3):
    yy=149+i*168
    a.rect(36,yy,540,153,['#E8F2E8','#FDF0DD','#E7F0F2'][i],r=20)
    circnum(i+1,56,yy+21,r=10)
    clipped_scene(83,yy+6,141,141,lambda i=i:picture(IMAGES/'positions.png',0,0,141,141,(i*512,0,(i+1)*512,512)),r=14)
    a.text(['The ball is ___ the tree.','The ball is ___ the box.','The ball is ___ the bench.'][i],265,yy+35,18,'Body')
    opts=[['under','in','behind'],['behind','under','in'],['in','behind','under']][i]
    for j,option in enumerate(opts):
        xx=269+j*98
        a.oval(xx,yy+93,12,12,None,INK,1.4)
        a.text(option,xx+18,yy+90,14,'BodyBold')
a.rect(36,670,540,59,TEAL,r=18)
a.text('Say the whole sentence!',306,689,21,'Round','#FFFFFF',align='center')
end()

# 11. Comprehension followed by an open drawing task.
start(11,'YOUR TURN','Read, draw, and tell','Circle your answers. Then make a picture of your own.')
a.rect(36,148,540,188,'#EAF1E4',r=21)
a.text('1. What color is Milo\'s ball?',57,170,20,'BodyBold')
for j,(word,col) in enumerate([('red',RED),('blue','#5A9DC5'),('yellow',YELLOW)]):
    xx=72+j*163
    a.oval(xx,205,20,20,col,INK,1)
    a.text(word,xx+31,205,17,'Body')
a.text('2. Who helps Milo?',57,257,20,'BodyBold')
for xx,word in [(73,'Pip'),(230,'a cat'),(406,'a fish')]:
    a.oval(xx,295,13,13,None,INK,1.4)
    a.text(word,xx+23,291,17,'Body')
a.text('3. Draw a ball. Give it a hiding place.',37,358,20,'BodyBold')
a.rect(36,397,540,229,'#FFFFFF','#ABC5BA',r=20,sw=1.6)
# Small corner decorations leave the drawing area open and usable.
a.sparkle(560,416,.6,'#D9E5D4')
a.text('My ball is',45,655,21,'Body')
a.line(161,678,546,678,INK,1.4)
a.text('Try: under the tree / in the box / behind the bench',45,693,13,'Body',MUTED)
a.text('Tell a friend about your picture.',45,716,15,'BodyBold',TEAL)
end()

# 12. An adult guide with the actual generated audio timings and answer key.
start(12,'FOR GROWN-UPS','Read together','A short, playful English lesson for ages 5-7.')
a.rect(36,146,540,137,'#E8F1E5',r=20)
a.text('A simple 15-minute lesson',55,162,21,'Round',TEAL)
guide=[('2 min','Meet Milo and Pip on page 2.'),('5 min','Play the story audio. Read pages 3-8 together.'),('4 min','Practise the words and phrases on pages 9-10.'),('4 min','Draw, tell, and celebrate on page 11.')]
for i,(time,action) in enumerate(guide):
    y=198+i*19
    a.text(time,55,y,12,'BodyBold',TEAL)
    a.text(action,108,y,12,'Body')

a.text('Audio companions',37,307,22,'Round')
a.text('Read along: '+stamp_time(META['story']['duration'])+'   |   Listen and repeat: '+stamp_time(META['practice']['duration']),37,339,13,'BodyBold',TEAL)
a.wrap('In the ebook, play one page at a time or choose Read to me. The downloadable story track announces page turns. The practice track leaves time for the child to speak.',37,365,533,12,16)
for i,item in enumerate(BOOK['story']):
    row,col=divmod(i,3)
    xx=37+col*183; yy=425+row*34
    a.rect(xx,yy,172,27,'#EDF0E6',r=8)
    a.text('Page '+str(item['page'])+'  '+stamp_time(META['story']['page_starts'][str(item['page'])]),xx+86,yy+7,11,'BodyBold',align='center')

a.text('Teaching tips',37,506,21,'Round')
a.wrap('Point to each panel in order: 1, then 2. Let the child echo a short line. Use a real ball and box to act out under, in, and behind. Accept pointing before speaking.',37,537,531,12,16)
a.wrap('The downloadable story track reads the titles, captions, and speech bubbles on pages 3-8. Ebook page audio also practises the SAY IT lines. Help with activity instructions as needed.',37,592,531,11,15)

a.rect(36,653,540,75,'#FCEAD6',r=17)
a.text('Answer key',54,667,16,'Round')
a.text('Page 10: 1 under; 2 in; 3 behind.',54,691,11,'Body')
a.text('Page 11: 1 red; 2 Pip; 3 any matching picture and sentence.',54,709,11,'Body')
end()

c.save()
print(str(OUT))
