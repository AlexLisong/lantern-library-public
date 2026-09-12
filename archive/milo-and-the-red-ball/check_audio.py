from pathlib import Path
import json
import os
os.environ['HF_HUB_OFFLINE']='1'
import numpy as np
import soundfile as sf
import torch
import whisper
torch.set_num_threads(4)
base=Path(__file__).resolve().parent
model=whisper.load_model('base.en',device='cpu')
checks=[]
for name in ['milo-and-the-red-ball-read-along','milo-and-the-red-ball-listen-and-repeat']:
    source=base/(name+'.wav')
    samples,rate=sf.read(source)
    assert np.isfinite(samples).all()
    assert 100<len(samples)/rate<240
    assert np.max(np.abs(samples))<0.999
    result=model.transcribe(str(source),fp16=False,language='en',initial_prompt='Milo and the Red Ball. Milo is a rabbit. Pip is a bird.',verbose=False)
    (base/(name+'-asr.json')).write_text(json.dumps(result,indent=2))
    checks.append({'name':name,'seconds':len(samples)/rate,'peak':float(np.max(np.abs(samples))),'transcript':result['text']})
(base/'audio-checks.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
