from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',25)
canvas=Image.new('RGB',(1200,910),'#292929');draw=ImageDraw.Draw(canvas)
for x,name,label in [(0,'baseline','v1.4.0 原始比例'),(600,'final','v1.4.2 头部放大20% · 无水袖')]:
 canvas.paste(Image.open(ROOT/f'reports/appearance_{name}_rest_front.png').convert('RGB'),(x,60));draw.text((x+25,15),label,font=font,fill='white')
canvas.save(ROOT/'reports/appearance_comparison.png')
