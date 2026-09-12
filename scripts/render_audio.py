"""Offline Kokoro narration with a sentence cache and exact page cue timings."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
from catalog import ROOT

def render(slug,voice=None):
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline
    folder=ROOT/'books'/slug;book=json.loads((folder/'book.json').read_text())
    selected=voice or book.get('voice','af_heart').removeprefix('Kokoro ');speed=book.get('speed',.96);sr=24000
    cache=ROOT/'.build/speech-cache';cache.mkdir(parents=True,exist_ok=True)
    pipeline=KPipeline(lang_code='a',repo_id='hexgrad/Kokoro-82M',device='cpu')
    for page in book['pages']:
        parts=[np.zeros(int(.25*sr),dtype=np.float32)];samples=len(parts[0]);cues=[]
        for line in page['narration']:
            key=hashlib.sha256(f'{selected}|{speed}|{line["text"]}'.encode()).hexdigest();wav=cache/(key+'.wav')
            if wav.exists():audio,rate=sf.read(wav,dtype='float32');assert rate==sr
            else:
                chunks=[np.asarray(result.audio,dtype=np.float32) for result in pipeline(line['text'],voice=selected,speed=speed) if result.audio is not None]
                if not chunks:raise ValueError('Kokoro returned no speech')
                audio=np.concatenate(chunks);sf.write(wav,audio,sr)
            if not np.isfinite(audio).all() or np.max(np.abs(audio))<.001:raise ValueError('Invalid speech signal')
            start=samples/sr;parts.append(audio);samples+=len(audio);cues.append({'text':line['text'],'start':round(start,3),'end':round(samples/sr,3),'page':page['number']})
            silence=np.zeros(round(line.get('pause',.65)*sr),dtype=np.float32);parts.append(silence);samples+=len(silence)
        pagewav=cache/f'{slug}-{page["number"]:02}.wav';sf.write(pagewav,np.concatenate(parts),sr)
        dest=folder/page['audio'];dest.parent.mkdir(exist_ok=True)
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(pagewav),'-af','loudnorm=I=-18:TP=-1.5:LRA=7','-ar',str(sr),'-ac','1','-c:a','libmp3lame','-b:a','96k',str(dest)],check=True)
        page.update(cues=cues,duration=round(samples/sr,3));print('Rendered page',page['number'],flush=True)
    book['voice']='Kokoro '+selected
    for dependent in ['storyTrack','practiceTrack','video','subtitles']:
        book.pop(dependent,None)
    (folder/'book.json').write_text(json.dumps(book,ensure_ascii=False,indent=2)+'\n')
    print('Page audio and exact sentence timings updated. Old companion/video references were invalidated; regenerate them before republishing those formats.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('slug');p.add_argument('--voice');a=p.parse_args();render(a.slug,a.voice)
