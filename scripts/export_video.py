"""Make a captioned 1080p read-along video from an ebook's illustrated panels."""
import argparse,json,subprocess,re
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
from catalog import ROOT

def font(size,bold=False):
    choices=[Path('/System/Library/Fonts/Supplemental/'+('Trebuchet MS Bold.ttf' if bold else 'Trebuchet MS.ttf')),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf')]
    for p in choices:
        if p.exists():return ImageFont.truetype(str(p),size)
    return ImageFont.load_default(size=size)

def wrap(text,draw,f,width):
    lines=[];line=''
    for word in text.split():
        trial=(line+' '+word).strip()
        if draw.textlength(trial,font=f)>width and line:lines.append(line);line=word
        else:line=trial
    if line:lines.append(line)
    return lines

def stamp(seconds):
    ms=round(seconds*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'

def export(slug,encoder):
    folder=ROOT/'books'/slug;book=json.loads((folder/'book.json').read_text());track=book.get('storyTrack')
    if not track:raise ValueError('Set storyTrack.file, duration and cues in book.json before video export (see docs/video.md)')
    work=ROOT/'.build'/slug/'video';work.mkdir(parents=True,exist_ok=True);out=folder/'video';out.mkdir(exist_ok=True)
    config_path=folder/'source/video-scenes.json'
    if not config_path.exists():raise ValueError('Create source/video-scenes.json with timed scene images; see docs/video.md')
    scenes=json.loads(config_path.read_text())
    frames=[];cue_font=font(42);heading_font=font(31,True);small_font=font(23,True)
    cues=track['cues'];duration=track['duration'];subs=[]
    for i,cue in enumerate(cues):
        start=0 if i==0 else cue['start'];end=cues[i+1]['start'] if i+1<len(cues) else duration
        scene=next((s for s in reversed(scenes) if s['start']<=start),scenes[0])
        source=(folder/scene['image']).resolve()
        if not source.is_relative_to(folder.resolve()):raise ValueError('Unsafe scene path')
        im=Image.open(source).convert('RGB')
        if scene.get('crop'):im=im.crop(scene['crop'])
        canvas=Image.new('RGB',(1920,1080),'#102b40');draw=ImageDraw.Draw(canvas)
        draw.text((96,43),book['title'].upper(),font=small_font,fill='#e6bc7a')
        draw.text((1824,43),'LANTERN LIBRARY',font=small_font,fill='#b1c7ce',anchor='ra')
        if scene.get('fit')=='contain':
            im=ImageOps.pad(im,(1728,576),color='#102b40',method=Image.Resampling.LANCZOS)
        elif scene.get('cover'):
            im=ImageOps.fit(im,(1728,600),method=Image.Resampling.LANCZOS)
        else:im=ImageOps.fit(im,(1728,576),method=Image.Resampling.LANCZOS)
        canvas.paste(im,(96,102))
        draw.text((96,720),scene.get('title',book['title']),font=heading_font,fill='#e6bc7a')
        text=cue['text'];lines=wrap(text,draw,cue_font,1680)
        if len(lines)>4:raise ValueError('Caption too long; split its narration cue')
        for j,line in enumerate(lines):draw.text((96,793+j*55),line,font=cue_font,fill='#fffaf0')
        draw.rectangle((96,1040,1824,1043),fill='#294553');draw.rectangle((96,1040,96+int(1728*end/duration),1043),fill='#cda05e')
        name=work/f'frame-{i:04}.png';canvas.save(name);frames.append((name,end-start))
        subs.append(f'{i+1}\n{stamp(cue["start"])} --> {stamp(cue["end"])}\n{text}\n')
    concat=work/'frames.txt'
    concat.write_text(''.join(f"file '{p.name}'\nduration {d:.3f}\n" for p,d in frames)+f"file '{frames[-1][0].name}'\n")
    srt=out/(slug+'.srt');srt.write_text('\n'.join(subs))
    mp4=out/(slug+'-1080p.mp4')
    cmd=['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(folder/track['file']),'-vf','fps=24','-c:v',encoder]
    cmd+=['-b:v','4000k'] if encoder=='h264_videotoolbox' else ['-preset','veryfast','-crf','23']
    cmd+=['-pix_fmt','yuv420p','-ar','48000','-c:a','aac','-b:a','160k','-movflags','+faststart','-t',str(duration),str(mp4)]
    subprocess.run(cmd,check=True)
    book['video']=str(mp4.relative_to(folder));book['subtitles']=str(srt.relative_to(folder));(folder/'book.json').write_text(json.dumps(book,ensure_ascii=False,indent=2)+'\n')
    print(mp4,flush=True);print(f'{len(frames)} captioned scenes, {duration:.1f} seconds. Subtitle file: {srt}',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('slug');p.add_argument('--encoder',default='libx264',choices=['libx264','h264_videotoolbox']);a=p.parse_args();export(a.slug,a.encoder)
