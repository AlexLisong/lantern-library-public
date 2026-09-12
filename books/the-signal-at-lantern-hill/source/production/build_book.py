"""Illustrated intermediate reader, with all learning text shared with narration."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
BOOK_DIR=BASE.parents[1]
BOOK=json.loads((BASE/'book.json').read_text())
LEARN=json.loads((BASE/'learning.json').read_text())
ART=BOOK_DIR/'source/illustrations'
OUT=BOOK_DIR/'downloads/the-signal-at-lantern-hill.pdf'
CROPS=json.loads((BOOK_DIR/'source/prompts/panel-crops.json').read_text()) if (BOOK_DIR/'source/prompts/panel-crops.json').exists() else {}
PRINT=BASE/'print-images';PRINT.mkdir(parents=True,exist_ok=True)
FONT='/System/Library/Fonts/Supplemental/'
if not Path(FONT).exists():FONT='/usr/share/fonts/truetype/dejavu/'
FALLBACK={'Text':'DejaVuSans.ttf','Bold':'DejaVuSans-Bold.ttf','Serif':'DejaVuSerif.ttf','Title':'DejaVuSerif-Bold.ttf'}
for name,file in [('Text','Trebuchet MS.ttf'),('Bold','Trebuchet MS Bold.ttf'),('Serif','Georgia.ttf'),('Title','Georgia Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,FONT+(file if Path(FONT+file).exists() else FALLBACK[name])))
INK='#19364A';TEAL='#286567';GOLD='#C58A36';PAPER='#FAF7EF';PALE='#E7EDEF';MUTED='#566E77';LINE='#CCD8DA'
c=canvas.Canvas(str(OUT),pagesize=(612,792),pageCompression=1)
c.setTitle(BOOK['title']);c.setAuthor('Original English Reader');c.setSubject('Illustrated mystery and intermediate English activities for ages 10-12')
page_no=0
metrics=[]

def rect(x,y,w,h,color,stroke=None,r=0):
    if color:c.setFillColor(HexColor(color))
    if stroke:c.setStrokeColor(HexColor(stroke));c.setLineWidth(.7)
    if r:c.roundRect(x,y,w,h,r,fill=bool(color),stroke=bool(stroke))
    else:c.rect(x,y,w,h,fill=bool(color),stroke=bool(stroke))

def line(x,y,x2,y2,color=LINE,width=.7):
    c.setStrokeColor(HexColor(color));c.setLineWidth(width);c.line(x,y,x2,y2)

def text(s,x,y,size=14,font='Text',color=INK,align='left'):
    c.saveState();c.translate(x,y);c.scale(1,-1);c.setFillColor(HexColor(color));c.setFont(font,size)
    if align=='right':c.drawRightString(0,-size*.84,s)
    elif align=='center':c.drawCentredString(0,-size*.84,s)
    else:c.drawString(0,-size*.84,s)
    c.restoreState()

def para(s,x,y,w,size=14.2,leading=None,color=INK,font='Text',max_h=None):
    original=size
    while True:
        lead=leading or size*1.31
        p=Paragraph(escape(s),ParagraphStyle('body',fontName=font,fontSize=size,leading=lead,textColor=HexColor(color),spaceBefore=0,spaceAfter=0))
        ww,hh=p.wrap(w,900)
        if max_h is None or hh<=max_h+.2:break
        size-=.2
        if size<11.8:raise ValueError((page_no,'Text does not fit',s,hh,max_h))
    c.saveState();c.translate(x,y+hh);c.scale(1,-1);p.drawOn(c,0,0);c.restoreState()
    metrics.append({'page':page_no,'text':s[:55],'top':y,'bottom':round(y+hh,2),'font':round(size,2)})
    if y+hh>748:raise ValueError((page_no,'Text crosses safe bottom',s,y+hh))
    return hh

def picture(path,x,y,w,h,crop=None):
    im=Image.open(path).convert('RGB')
    if crop:im=im.crop(crop)
    target=(round(w*2.84),round(h*2.84))
    im=ImageOps.fit(im,target,method=Image.Resampling.LANCZOS)
    name=Path(path).stem+'-'+str(int(y))+'-'+str(int(w))+'-'+('-'.join(map(str,crop)) if crop else 'full')+'.jpg'
    dest=PRINT/name;im.save(dest,quality=93,subsampling=0)
    c.saveState();c.translate(x,y+h);c.scale(1,-1);c.drawImage(str(dest),0,0,w,h);c.restoreState()

def start(n,section,title,subtitle=None):
    global page_no
    page_no=n;c.saveState();c.translate(0,792);c.scale(1,-1)
    rect(0,0,612,792,PAPER)
    text('LANTERN HILL',36,25,9,'Bold',TEAL)
    text(section,576,25,9,'Bold',MUTED,'right')
    line(36,46,576,46)
    if title:text(title,36,65,27,'Title')
    if subtitle:para(subtitle,36,107,540,13.4,color=MUTED,max_h=39)

def end():
    line(36,755,576,755)
    text(BOOK['title'],36,766,8.5,color=MUTED)
    text(str(page_no).zfill(2),576,763,12,'Bold',TEAL,'right')
    c.restoreState();c.showPage()

def think(s,y=705):
    rect(36,y,540,43,PALE,r=5)
    text('PAUSE & THINK',48,y+14,9.2,'Bold',TEAL)
    para(s,149,y+5,413,12.2,max_h=33)

def section(title,s,x,y,w=540,size=14):
    text(title,x,y,16,'Bold',TEAL)
    h=para(s,x,y+25,w,size)
    return y+25+h+20

def num_panel(n,y):
    rect(21,y+8,25,22,INK,r=3)
    text(str(n),33.5,y+13,10,'Bold','#FFFFFF','center')

# Cover.
start(1,'','')
rect(0,0,612,246,INK)
text('AN ILLUSTRATED MYSTERY',36,35,11,'Bold','#E9BA71')
text('THE SIGNAL',33,80,46,'Title','#FFFFFF')
text('AT LANTERN HILL',34,138,37,'Title','#FFFFFF')
text(BOOK['subtitle'],37,207,15,'Text','#D9E7EA')
picture(ART/'cover.png',0,246,612,408)
text('Read the clues. Challenge your assumptions.',36,682,18,'Bold')
text(BOOK['audience'],36,718,13,'Text',TEAL)
end()

# Reader briefing.
item=LEARN['2'];start(2,item['section'],item['title'],item['note'])
for i,(name,desc,crop) in enumerate([
    ('Milo',item['sections'][0]['items'][0],(285,130,750,675)),
    ('Pip',item['sections'][0]['items'][1],(925,605,1185,915))
]):
    x=36+i*278;rect(x,151,262,190,'#E8EEEA',r=7)
    picture(ART/'cover.png',x+15,165,76,95,crop)
    text(name,x+107,174,24,'Title')
    para(desc,x+107,213,140,12.8,max_h=115)
text('Your reading mission',36,365,19,'Title')
for i,entry in enumerate(item['sections'][1]['items']):
    label,body=entry.split(': ',1);x=36+i*184
    text('0'+str(i+1),x,404,12,'Bold',GOLD)
    text(label,x+24,401,17,'Bold')
    para(body,x,431,163,13.2,max_h=60)
y=section('Read and listen',item['sections'][2]['text'],36,500,size=13.2)
section('After the mystery',item['sections'][3]['text'],36,y,size=13.2)
think(item['sections'][4]['text'])
end()

# Eight two-panel chapters.
for story in BOOK['story']:
    n=story['page'];start(n,'CHAPTER '+str(story['chapter']).zfill(2),story['title'])
    key='page-'+str(n).zfill(2);img=ART/(key+'.png')
    crop=CROPS.get(key,{'top':[0,0,1536,496],'bottom':[0,532,1536,1024]})
    picture(img,36,109,540,174,crop['top']);num_panel(1,109)
    para(story['panels'][0],43,296,526,14.5,max_h=89)
    if story.get('poem'):
        picture(img,36,400,540,158,crop['bottom']);num_panel(2,400)
        rect(36,574,248,121,'#F4E9D2',r=4)
        text('THE STONE TABLET',49,583,9,'Bold',TEAL)
        for i,poemline in enumerate(story['poem']):text(poemline,49,606+i*16.5,12.4,'Serif')
        para(story['panels'][1],302,578,274,12.9,max_h=116)
    else:
        picture(img,36,400,540,174,crop['bottom']);num_panel(2,400)
        para(story['panels'][1],43,587,526,14.5,max_h=106)
    think(story['think']);end()

# Vocabulary: contextual examples keep the words connected to the mystery.
item=LEARN['11'];start(11,item['section'],item['title'],item['note'])
for i,v in enumerate(BOOK['vocabulary']):
    row,col=divmod(i,2);x=36+col*278;y=151+row*147
    rect(x,y,262,133,'#EAF0EE' if col==0 else '#F3EBDD',r=6)
    text(v['word'],x+15,y+13,19,'Title')
    h=para(v['definition'],x+15,y+43,232,12.8,max_h=39)
    para(v['example'],x+15,y+48+h,232,11.9,color=MUTED,max_h=34)
text('Use three new words',36,610,17,'Bold',TEAL)
para(item['sections'][0]['text'],36,637,540,13.2,max_h=54)
para(item['sections'][1]['text'],36,710,540,12.5,max_h=36)
end()

# Evidence and inference worksheet.
item=LEARN['12'];start(12,item['section'],item['title'],item['note'])
s=item['sections'][0];rect(36,151,540,187,'#EAF0EE',r=6)
text(s['title'],49,166,17,'Bold',TEAL)
para(s['text'],49,194,514,12.9,max_h=35)
for i,entry in enumerate(s['items']):text(entry,49,238+i*22,13.5)
text(item['sections'][1]['title'],36,366,17,'Bold',TEAL)
for i,entry in enumerate(item['sections'][1]['items']):
    x=36+i*278;para(entry,x,397,260,13.5,max_h=74)
    line(x,484,x+260,484);line(x,508,x+260,508)
for col,idx in enumerate([2,3]):
    x=36+col*278;s=item['sections'][idx]
    text(s['title'],x,547,16,'Bold',TEAL)
    para(s['text'],x,576,260,13.1,max_h=93)
    line(x,685,x+260,685);line(x,714,x+260,714)
end()

# Language worksheet.
item=LEARN['13'];start(13,item['section'],item['title'],item['note'])
s=item['sections'][0];text(s['title'],36,152,16,'Bold',TEAL)
para(s['text'],36,181,540,13.2,max_h=58)
rect(36,247,540,39,'#EAF0EE',r=4)
para(s['items'][0],48,258,516,13.2,max_h=25)
s=item['sections'][1];text(s['title'],36,312,16,'Bold',TEAL)
para(s['text'],36,340,540,12.8,max_h=34)
for i,entry in enumerate(s['items']):
    y=382+i*56;rect(36,y,540,46,'#EAF0EE',r=4);para(entry,48,y+8,516,13.2,max_h=34)
s=item['sections'][2];text(s['title'],36,508,16,'Bold',TEAL)
para(s['text'],36,536,540,12.6,max_h=33)
para(s['items'][0],48,577,516,13.2,max_h=34)
para(s['items'][1],48,613,516,13.2,max_h=34)
s=item['sections'][3];text(s['title'],36,674,16,'Bold',TEAL)
para(s['text'],36,699,540,12.2,max_h=48)
end()

# Writing page with substantial writing space.
item=LEARN['14'];start(14,item['section'],item['title'],item['note'])
text('Your starting point',36,152,17,'Bold',TEAL)
para(item['sections'][0]['text'],36,179,540,14,max_h=57)
for col,idx in enumerate([1,2]):
    x=36+col*278;text(item['sections'][idx]['title'],x,251,16,'Bold',TEAL)
    y=279
    for i,entry in enumerate(item['sections'][idx]['items']):
        h=para(str(i+1)+'. '+entry,x,y,258,12.4,max_h=35);y+=h+8
text('Your scene',36,443,17,'Bold',TEAL)
text('Write here or on a separate sheet.',576,448,10,'Text',MUTED,'right')
for y in range(490,711,20):line(36,y,576,y,'#CDD6D3')
para(item['sections'][3]['text'],36,722,540,11.5,max_h=24)
end()

# Answer key and teaching guide.
for number in [15,16]:
    item=LEARN[str(number)];start(number,item['section'],item['title'],item['note'])
    y=153
    for s in item['sections']:
        text(s['title'],36,y,16,'Bold',TEAL);y+=25
        if s.get('text'):y+=para(s['text'],36,y,540,12.9)+12
        for entry in s.get('items',[]):y+=para(entry,44,y,532,12.9)+9
        y+=10
    end()

c.save()
(BASE/'layout-metrics.json').write_text(json.dumps(metrics,indent=2))
print(OUT)
print('16 pages created; paragraph bounds checked.')
