"""Create an unpublished book with an editable manuscript and asset folders."""
import argparse,json,re
from pathlib import Path
from catalog import ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('slug');p.add_argument('--title',required=True);p.add_argument('--level',default='Intermediate');p.add_argument('--age-min',type=int,default=10);p.add_argument('--age-max',type=int,default=12);a=p.parse_args()
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',a.slug):p.error('Use lowercase words separated by hyphens')
    folder=ROOT/'books'/a.slug
    if folder.exists():p.error('Book already exists; refusing to overwrite it')
    for name in ['pages','audio','downloads','source/illustrations','source/prompts']: (folder/name).mkdir(parents=True,exist_ok=True)
    book={'schemaVersion':1,'status':'draft','slug':a.slug,'title':a.title,'description':'Add a short reader-facing description.','audience':f'Ages {a.age_min}–{a.age_max} · {a.level} English','ageMin':a.age_min,'ageMax':a.age_max,'level':a.level,'genre':'Adventure','voice':'af_heart','speed':.96,'accent':'#286567','cover':'pages/page-01.webp','pdf':f'downloads/{a.slug}.pdf','pages':[]}
    (folder/'book.json').write_text(json.dumps(book,indent=2)+'\n')
    manuscript={'pages':[{'layout':'cover','title':a.title,'section':'AN ILLUSTRATED ADVENTURE','illustration':'cover.png','paragraphs':['Write your cover subtitle.'],'tip':'Look closely at the cover. What might happen?'},{'layout':'story','title':'A new beginning','section':'CHAPTER 01','illustration':'page-02.png','panels':['Write the first scene here.','Write the second scene here.'],'question':'What do you predict will happen next?','autoNext':False},{'layout':'lesson','title':'Explore the story','section':'WORDS AND IDEAS','paragraphs':['Word: write a definition and an example.','Discuss: write a question that requires evidence from the story.','Write: add a creative challenge.'],'tip':'Support your answer with a detail from the story.'}]}
    (folder/'source/manuscript.json').write_text(json.dumps(manuscript,indent=2)+'\n')
    print(f'Created draft: {folder}\nEdit source/manuscript.json, add original artwork, then run render_pdf.py and render_audio.py. See docs/creating-books.md.')

if __name__=='__main__':main()
