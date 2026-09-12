import os
"""Produce independently playable, sentence-timed Kokoro audio for every ebook page."""
from pathlib import Path
import json
import shutil
from make_audio import Track, BOOK, BASE, OUT

SITE=Path(os.environ['LANTERN_LEGACY_SITE']).expanduser()
(SITE/'audio').mkdir(parents=True,exist_ok=True)

def meta(number,title,section,note,tip,lines):
    return {'number':number,'title':title,'section':section,'note':note,'tip':tip,'lines':lines}

pages=[
    meta(1,BOOK['title'],'A LITTLE ADVENTURE','A story about a lost ball and a helpful friend.','Point to Milo. Can you find the red ball?',[
        (BOOK['title']+'.',1),
        (BOOK['subtitle']+'.',1),
        ('Read. Look. Say.',1.3),
        ('Let us read together. Turn the page when you are ready.',2)]),
    meta(2,'Hello, friends!','MEET THE FRIENDS','Meet Milo the rabbit and Pip the bird.','Say hello to Milo and Pip. What animal is Milo?',[
        ('Hello, friends!',1),('Point to Milo. Point to Pip. Say hello!',2),
        ('Milo is a rabbit. Hello!',1.2),('Pip is a bird. Hi!',1.2),
        ('Ready to read?',1),('Look at the pictures.',1),('Listen to the story.',1),('Read and say the words.',2)])
]
notes={3:('Meet two friends on a sunny day.','Say “Let’s play!” to someone you like.'),4:('Oh, no! The ball rolls away.','Show a surprised face. Where did the ball go?'),5:('Look carefully under the tree.','Point to the red leaf. Is it a ball?'),6:('What is hiding in the box?','Point to the hat. What color is it?'),7:('Pip has spotted something red.','Look behind the bench. Can you see the ball?'),8:('A happy ending for two good friends.','Practise “Thank you!” and “You’re welcome!”')}
for story in BOOK['story']:
    heading=story['title'] if story['title'].endswith(('!','?','.')) else story['title']+'.'
    lines=[(heading,1)]
    for panel in story['panels']:
        if panel['caption']: lines.append((panel['caption'],.85))
        lines.extend((line,1) for line in panel['speech'])
    lines.extend([('Now you say: '+story['say'],4)])
    number=story['page']; note,tip=notes[number]
    pages.append(meta(number,story['title'],'STORY TIME',note,tip,lines))
pages.extend([
    meta(9,'Picture words','LOOK AND SAY','Listen, point, and say each word.','Find these six things in the story.',
        [('Picture words.',1),('Listen, point, and say each word.',1.5)]+[(word.capitalize()+'. Your turn.',3.5) for word in BOOK['words']]+[('Can you find it?',1),('Find a red leaf in the story.',2),('Find a red hat. Find the red ball!',2)]),
    meta(10,'Where is the ball?','PLAY WITH WORDS','Look at the pictures and choose the words.','Use a real ball and a box to try “in” and “under.”',[
        ('Where is the ball?',1),('Look at each picture. Circle the correct word.',2),
        ('One. The ball is where? Under, in, or behind the tree?',5),
        ('Two. The ball is where? Behind, under, or in the box?',5),
        ('Three. The ball is where? In, behind, or under the bench?',5),
        ('Say the whole sentence!',4)]),
    meta(11,'Read, draw, and tell','YOUR TURN','Choose your answers, then draw your own hiding place.','Use paper and crayons for your picture.',[
        ('Read, draw, and tell.',1),('Circle your answers. Then make a picture of your own.',2),
        ('One. What color is Milo\'s ball? Red, blue, or yellow?',5),
        ('Two. Who helps Milo? Pip, a cat, or a fish?',5),
        ('Three. Draw a ball. Give it a hiding place.',3),
        ('My ball is ...',3),('Try: under the tree, in the box, or behind the bench.',3),
        ('Tell a friend about your picture.',3)]),
    meta(12,'Read together','FOR GROWN-UPS','A playful lesson, with a little help from you.','Celebrate effort. Pointing is a good first step toward speaking.',[
        ('Read together. For grown-ups.',1),('A short, playful English lesson for ages five to seven.',1),
        ('Meet Milo and Pip on page two.',1),('Play the story audio. Read pages three to eight together.',1),
        ('Practise the words and phrases on pages nine and ten.',1),('Draw, tell, and celebrate on page eleven.',1),
        ('In the ebook, play one page at a time. Read to me turns the pages automatically.',1.5),
        ('Point to each panel in order: one, then two. Let the child echo a short line.',1),
        ('Use a real ball and box to act out under, in, and behind. Accept pointing before speaking.',1.5),
        ('Help with the activity instructions as needed.',1),
        ('Answer key. Page ten: one, under. Two, in. Three, behind.',1),
        ('Page eleven: one, red. Two, Pip. Three, any matching picture and sentence.',1),
        ('You finished the book. Lovely reading!',2)])
])

for page in pages:
    track=Track();track.silence(.25)
    for line,pause in page.pop('lines'):
        track.line(line,pause=pause,page=page['number'])
    stem='page-'+str(page['number']).zfill(2)
    result=track.save('pages/'+stem,title=BOOK['title']+' - Page '+str(page['number']))
    shutil.copy2(result['file'],SITE/'audio'/(stem+'.mp3'))
    page.update({'audio':'audio/'+stem+'.mp3','image':'pages/'+stem+'.webp','thumbnail':'pages/'+stem+'-thumb.webp','duration':result['duration'],'cues':result['cues'],'alt':f'Page {page["number"]}: {page["title"]}. Illustrated English story page. The readable text and narration are beside the page.'})
    print(stem,result['duration'],'seconds',flush=True)
data={'title':BOOK['title'],'voice':'Kokoro af_heart','pages':pages}
(BASE/'page-audio-metadata.json').write_text(json.dumps(data,indent=2))
(SITE/'book-data.js').write_text('window.BOOK = '+json.dumps(data,ensure_ascii=False,indent=2)+';\n')
print('Created 12 page tracks and ebook cue data.',flush=True)
