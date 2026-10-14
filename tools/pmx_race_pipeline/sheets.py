"""Static inspection contact sheets; source/final images remain separate artifacts."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,sys
from context import SERIES,config
def sheets(mode='source'):
    batch=json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'));rows=batch['characters'];out=SERIES/'reports';out.mkdir(exist_ok=True);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    for label in (['bow_worst','riding_worst','facegen_worst'] if mode=='motion' else ['front','back']):
        for page,start in enumerate(range(0,len(rows),12),1):
            selected=rows[start:start+12];canvas=Image.new('RGB',(4*260,3*390),(55,59,66));draw=ImageDraw.Draw(canvas)
            for i,row in enumerate(selected):
                root=Path(row['root']);c=config(root);name=f'source_{label}.png' if mode=='source' else f'final_{label}.png' if mode=='motion' else f'final_rest_{label}.png';path=root/'reports'/name
                if path.exists():
                    im=Image.open(path).convert('RGBA');im.thumbnail((252,352));tile=Image.new('RGBA',im.size,(55,59,66,255));tile.alpha_composite(im);x=(i%4)*260+(260-im.width)//2;y=(i//4)*390;canvas.paste(tile.convert('RGB'),(x,y))
                draw.text(((i%4)*260+8,(i//4)*390+357),c['display_name'],font=font,fill='white')
            dest=out/f'{mode}_{label}_{page}.png';canvas.save(dest);print(dest)
if __name__=='__main__':sheets(sys.argv[1] if len(sys.argv)>1 else 'source')
