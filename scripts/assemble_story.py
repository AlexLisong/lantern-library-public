"""Join chapter page audio and adjust sentence timestamps for video export."""
import argparse,json,subprocess
from pathlib import Path
from catalog import ROOT

def assemble(slug):
    folder=ROOT/'books'/slug;book=json.loads((folder/'book.json').read_text());work=ROOT/'.build'/slug/'story';work.mkdir(parents=True,exist_ok=True)
    chapters=[p for p in book['pages'] if p['section'].upper().startswith('CHAPTER')]
    if not chapters:raise ValueError('Mark story pages with a CHAPTER section')
    cues=[];starts={};offset=0;parts=[];scenes=[]
    for page in chapters:
        stop=next((c['start'] for c in page['cues'] if c['text'].lower().startswith('pause and think')),page['duration'])
        sample_count=round(stop*24000);stop=sample_count/24000
        wav=work/f'page-{page["number"]:02}.wav'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(folder/page['audio']),'-af',f'atrim=end_sample={sample_count}', '-ar','24000','-ac','1',str(wav)],check=True)
        parts.append(wav);starts[str(page['number'])]=round(offset,3)
        for cue in page['cues']:
            if cue['end']<=stop:cues.append({**cue,'start':round(offset+cue['start'],3),'end':round(offset+cue['end'],3),'page':page['number']})
        scenes.append({'start':round(offset,3),'image':page['image'],'title':page['title'],'fit':'contain'})
        offset+=stop
    concat=work/'concat.txt';concat.write_text(''.join(f"file '{p.name}'\n" for p in parts))
    dest=folder/'audio'/(slug+'-story.mp3')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c:a','libmp3lame','-b:a','96k',str(dest)],check=True)
    book['storyTrack']={'file':str(dest.relative_to(folder)),'duration':round(offset,3),'cues':cues,'page_starts':starts}
    for key in ['video','subtitles']:book.pop(key,None)
    (folder/'book.json').write_text(json.dumps(book,ensure_ascii=False,indent=2)+'\n')
    # Timing changes invalidate prior panel timings; preserve an archival copy before replacing.
    scenes_path=folder/'source/video-scenes.json'
    if scenes_path.exists():(folder/'source/video-scenes.previous.json').write_bytes(scenes_path.read_bytes())
    scenes_path.write_text(json.dumps(scenes,indent=2)+'\n')
    print('Created continuous story audio and default page scenes. Refine panel crops/timings in source/video-scenes.json, then export_video.py.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('slug');assemble(p.parse_args().slug)
