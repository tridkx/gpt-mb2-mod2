"""Contact sheet of final package previews for manual review."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project_paths import resolve_project
from PIL import Image,ImageDraw
import sys
root=resolve_project(Path(__file__).resolve().parents[1],sys.argv[1])
names=['rest_front','rest_side','rest_back','run_contact','riding_worst','face_all']
out=Image.new('RGB',(1800,620),(32,32,32));draw=ImageDraw.Draw(out)
for i,name in enumerate(names):
    f=root/'reports'/('final_'+name+'.png')
    if not f.exists():
        f=root/'reports'/('final_'+name.replace('_contact','_worst')+'.png')
    im=Image.open(f);im.thumbnail((300,570));out.paste(im,(i*300,35));draw.text((i*300+8,10),name,fill='white')
out.save(root/'build/review_sheet.png')
print(root/'build/review_sheet.png')
