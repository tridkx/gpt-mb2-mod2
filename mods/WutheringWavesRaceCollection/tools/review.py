"""Create contact sheets from final-package previews and record their hashes."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
S=Path(__file__).resolve().parents[1]
ROWS=json.loads((S/'batch_inventory.json').read_text(encoding='utf8'))['characters']
def main():
 font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22);overview=Image.new('RGB',(1440,1040),'#292d33');draw=ImageDraw.Draw(overview)
 names=['rest_front','head','facegen_worst','run_worst','bow_worst','riding_worst','slash_worst','lod3_rest_front']
 hashes={}
 for index,row in enumerate(ROWS):
  root=S/row['id'];r=root/'reports';review=Image.new('RGB',(1440,960),'#252932');d=ImageDraw.Draw(review)
  for i,name in enumerate(names):
   p=r/('final_'+name+'.png');assert p.is_file(),p;review.paste(Image.open(p).convert('RGB').resize((360,460)),((i%4)*360,(i//4)*480));d.text(((i%4)*360+10,(i//4)*480+462),name,fill='white');hashes[p.relative_to(S).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
  review.save(r/'visual_review.jpg')
  p=r/'final_rest_front.png';overview.paste(Image.open(p).convert('RGB').resize((360,460)),((index%4)*360,(index//4)*520));draw.text(((index%4)*360+15,(index//4)*520+472),row['name'],font=font,fill='white')
 overview.save(S/'reports/collection_overview.jpg')
 (S/'reports/preview_index.json').write_text(json.dumps({'source':'Final TPAC decoded geometry, textures and quantized weights','game_verified':False,'files_sha256':hashes},indent=2))
if __name__=='__main__':main()
