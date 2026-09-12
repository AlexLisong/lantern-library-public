"""Portable cover / two-panel comic / learning-page template for new books."""
import argparse,json,re,subprocess
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image,ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.colors import HexColor
from catalog import ROOT

def render(slug):
    folder=ROOT/'books'/slug
    book=json.loads((folder/'book.json').read_text());ms=json.loads((folder/'source/manuscript.json').read_text())
    temp=ROOT/'.build'/slug;temp.mkdir(parents=True,exist_ok=True)
    pdf=folder/book['pdf'];pdf.parent.mkdir(exist_ok=True)
    c=canvas.Canvas(str(pdf),pagesize=(612,792));c.setTitle(book['title']);pages=[]
    def paragraph(s,x,top,width,size=14,max_h=130):
        p=Paragraph(escape(s),ParagraphStyle('body',fontName='Helvetica',fontSize=size,leading=size*1.35,textColor=HexColor('#19364a')))
        _,h=p.wrap(width,900)
        if h>max_h:raise ValueError(f'Text does not fit on page {n}: shorten it or split the page')
        p.drawOn(c,x,792-top-h);return h
    def image(name,top,height,crop=None):
        path=(folder/'source/illustrations'/name).resolve()
        if not path.is_relative_to((folder/'source/illustrations').resolve()):raise ValueError('Unsafe illustration path')
        im=Image.open(path).convert('RGB')
        if crop:im=im.crop(crop)
        im=ImageOps.fit(im,(1080,int(height*2)),method=Image.Resampling.LANCZOS);out=temp/f'{n}-{top}.jpg';im.save(out,quality=95)
        c.drawImage(str(out),36,792-top-height,540,height)
    for n,page in enumerate(ms['pages'],1):
        c.setFillColor(HexColor('#faf7ef'));c.rect(0,0,612,792,fill=1,stroke=0)
        c.setFillColor(HexColor('#286567'));c.setFont('Helvetica-Bold',9);c.drawString(36,762,page.get('section',''))
        c.setFillColor(HexColor('#19364a'));c.setFont('Times-Bold',28);c.drawString(36,711,page['title'])
        spoken=[page['title']+'.'];layout=page['layout']
        if layout=='cover':
            image(page['illustration'],140,380)
            y=552
            for text in page.get('paragraphs',[]):y+=paragraph(text,36,y,540,max_h=120)+14;spoken.append(text)
            paragraph(book['audience'],36,705,540,12,max_h=25)
        elif layout=='story':
            im=Image.open(folder/'source/illustrations'/page['illustration']);w,h=im.size
            crops=page.get('crops',{'top':[0,0,w,h//2-8],'bottom':[0,h//2+8,w,h]})
            if len(page['panels'])!=2:raise ValueError('Story pages require two panels')
            for i,(text,top) in enumerate(zip(page['panels'],[111,402])):
                image(page['illustration'],top,172,crops['top' if i==0 else 'bottom'])
                paragraph(text,36,top+186,540,14,max_h=96);spoken.append(text)
            if page.get('question'):paragraph('Pause and think: '+page['question'],36,708,540,12,max_h=36);spoken.append('Pause and think. '+page['question'])
        elif layout=='lesson':
            y=132
            for text in page.get('paragraphs',[]):y+=paragraph(text,36,y,540,max_h=700-y)+24;spoken.append(text)
        else:raise ValueError(f'Unknown layout {layout}')
        c.setFont('Helvetica',9);c.drawString(36,22,book['title']);c.drawRightString(576,22,str(n));c.showPage()
        narration=[]
        for text in spoken:
            for sentence in re.findall(r'.+?(?:[.!?][\'\"]?(?=\s|$)|$)',text):
                if sentence.strip():narration.append({'text':sentence.strip(),'pause':.65})
        row={'number':n,'title':page['title'],'section':page.get('section',''),'note':page.get('question',page.get('paragraphs',[''])[0] if page.get('paragraphs') else ''),'tip':page.get('tip',page.get('question','Read at your own pace.')),'image':f'pages/page-{n:02}.webp','thumbnail':f'pages/page-{n:02}-thumb.webp','audio':f'audio/page-{n:02}.mp3','narration':narration,'cues':[],'duration':0,'alt':f'Page {n}: {page["title"]}. Full narration appears in Read along.'}
        if page.get('autoNext') is False:row.update(autoNext=False,stopMessage=page.get('stopMessage','Pause here before continuing.'))
        pages.append(row)
    c.save()
    for stale in temp.glob('page-*.png'):stale.unlink()
    subprocess.run(['pdftoppm','-r','144','-png',str(pdf),str(temp/'page')],check=True)
    (folder/'pages').mkdir(exist_ok=True)
    for n,path in enumerate(sorted(temp.glob('page-*.png')),1):
        im=Image.open(path).convert('RGB');im.save(folder/f'pages/page-{n:02}.webp',quality=92);im.thumbnail((244,316));im.save(folder/f'pages/page-{n:02}-thumb.webp',quality=85)
    book['pages']=pages
    for dependent in ['storyTrack','practiceTrack','video','subtitles']:book.pop(dependent,None)
    (folder/'book.json').write_text(json.dumps(book,ensure_ascii=False,indent=2)+'\n')
    print(f'Rendered {len(pages)} pages. Inspect the PDF and images, then generate narration. Status remains {book["status"]}.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('slug');render(p.parse_args().slug)
