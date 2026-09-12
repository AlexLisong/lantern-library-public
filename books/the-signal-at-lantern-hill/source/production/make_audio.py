"""One Kokoro track per page, plus a story track and vocabulary practice."""
from pathlib import Path
import json
import re
from voice import Track, BASE, BOOK, OUT

learning=json.loads((BASE/'learning.json').read_text())

def sentences(text):
    parts=re.findall(r'.+?(?:[.!?][\'\"]?(?=\s|$)|$)',text)
    return [x.strip() for x in parts if x.strip()]

def say_paragraph(track,text,page,pause=.38):
    for line in sentences(text): track.line(line,pause=pause,page=page)

pages=[]
cover=Track();cover.silence(.3)
for text in [BOOK['title']+'.',BOOK['subtitle']+'.','An illustrated mystery for intermediate English readers.','Read the clues. Challenge your assumptions.']:
    cover.line(text,pause=.7,page=1)
pages.append({'number':1,'title':BOOK['title'],'section':'AN ILLUSTRATED MYSTERY','note':'An old map. A hidden direction. A theory that needs testing.','tip':'What would convince you that your first explanation was wrong?','track':cover})

for number in range(2,17):
    track=Track();track.silence(.25)
    if 3<=number<=10:
        chapter=BOOK['story'][number-3]
        track.line('Chapter '+str(chapter['chapter'])+'. '+chapter['title']+'.',pause=.8,page=number)
        say_paragraph(track,chapter['panels'][0],number)
        track.silence(.5)
        if chapter.get('poem'):
            track.line('The inscription reads:',pause=.5,page=number)
            for line in chapter['poem']: track.line(line,pause=.8,page=number)
            track.silence(.5)
        say_paragraph(track,chapter['panels'][1],number)
        track.line('Pause and think. '+chapter['think'],pause=4,page=number)
        page={'number':number,'title':chapter['title'],'section':'CHAPTER '+str(chapter['chapter']).zfill(2),'note':chapter['think'],'tip':'Separate what the characters observe from what they assume.','track':track}
        if number==10:
            page['autoNext']=False
            page['stopMessage']='The story is complete. Choose the next page when you are ready for the activities.'
    else:
        item=learning[str(number)]
        track.line(item['title']+'.',pause=.7,page=number)
        say_paragraph(track,item['note'],number)
        if number==11:
            for word in BOOK['vocabulary']:
                track.line(word['word'].capitalize()+'.',pause=.55,page=number)
                say_paragraph(track,word['definition']+'.',number)
                say_paragraph(track,word['example'],number,pause=.9)
        for section in item['sections']:
            heading=re.sub(r'^\d+ / ','',section['title'])
            track.line(heading+'.',pause=.5,page=number)
            if section.get('text'): say_paragraph(track,section['text'],number)
            for text in section.get('items',[]):
                spoken=re.sub(r'_+','blank',text)
                if number==15 and spoken=='1. F, A, F, A.': spoken='One. Fact, assumption, fact, assumption.'
                say_paragraph(track,spoken,number,pause=1 if number in (12,13,14) else .4)
        track.silence(1)
        page={'number':number,'title':item['title'],'section':item['section'],'note':item['note'],'tip':item['tip'],'track':track}
        if number==14:
            page['autoNext']=False
            page['stopMessage']='Take time to write your scene. The next page contains suggested answers.'
    pages.append(page)

for page in pages:
    track=page.pop('track');stem='page-'+str(page['number']).zfill(2)
    result=track.save('pages/'+stem,title=BOOK['title']+' - Page '+str(page['number']))
    page.update({'audio':'audio/lantern-hill/'+stem+'.mp3','image':'pages/lantern-hill/'+stem+'.webp','thumbnail':'pages/lantern-hill/'+stem+'-thumb.webp','duration':result['duration'],'cues':result['cues'],'alt':f'Page {page["number"]}: {page["title"].rstrip(".!?")}. Illustrated intermediate English reader. Full text is available in the Read along panel.'})
    print('PAGE',page['number'],round(page['duration'],1),'seconds',flush=True)

full=Track();full.silence(.4);full.line(BOOK['title']+'.',pause=1)
full.line('The story begins on page three.',pause=1)
starts={}
for chapter in BOOK['story']:
    starts[str(chapter['page'])]=round(full.samples/24000,3)
    full.line('Chapter '+str(chapter['chapter'])+'. '+chapter['title']+'.',pause=.6,page=chapter['page'])
    say_paragraph(full,chapter['panels'][0],chapter['page'])
    if chapter.get('poem'):
        full.line('The inscription reads:',pause=.5,page=chapter['page'])
        for line in chapter['poem']: full.line(line,pause=.7,page=chapter['page'])
    say_paragraph(full,chapter['panels'][1],chapter['page'])
    full.silence(1)
    if chapter['page']!=10: full.line('Turn the page.',pause=1.5)
full.line('The end.',pause=1)
full_result=full.save(BOOK['slug']+'-story',title=BOOK['title']+' - Complete Story')
full_result['page_starts']=starts

practice=Track();practice.silence(.3)
practice.line(BOOK['title']+'. Vocabulary practice.',pause=.8)
practice.line('Listen to each word and its meaning. Then repeat the example sentence.',pause=1)
for word in BOOK['vocabulary']:
    practice.line(word['word'].capitalize()+'.',pause=.8)
    practice.line(word['definition']+'.',pause=.7)
    practice.line(word['example'],pause=.8)
    practice.line('Your turn.',pause=5)
practice.line('Now choose three of these words and use them in your own sentences.',pause=2)
practice_result=practice.save(BOOK['slug']+'-vocabulary',title=BOOK['title']+' - Vocabulary Practice')
data={'title':BOOK['title'],'slug':BOOK['slug'],'audience':BOOK['audience'],'voice':'Kokoro af_heart','pages':pages,'storyTrack':full_result,'practiceTrack':practice_result}
(BASE/'page-audio-metadata.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
(OUT/'audio-transcript.txt').write_text('\n\n'.join('PAGE '+str(p['number'])+' - '+p['title']+'\n'+'\n'.join(c['text'] for c in p['cues']) for p in pages))
print('All 16 page tracks and two companion tracks complete.',flush=True)
