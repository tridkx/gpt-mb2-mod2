"""Assemble source/final/LOD/motion images for visual inspection, without retouching."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
items=[('Source',R/'input/original/preview_full.png'),('Final LOD0',R/'reports/final_rest_front.png'),('UI idle',R/'reports/final_ui_neutral_female_worst.png'),('Face',R/'reports/final_head.png'),('Back',R/'reports/final_rest_back.png'),('Run',R/'reports/final_run_worst.png'),('Bow',R/'reports/final_bow_worst.png'),('Riding',R/'reports/final_riding_worst.png'),('Slash',R/'reports/final_slash_worst.png'),('LOD1',R/'reports/final_lod1_rest_front.png'),('LOD2',R/'reports/final_lod2_rest_front.png'),('LOD3',R/'reports/final_lod3_rest_front.png')]
sheet=Image.new('RGB',(1600,1500),(45,45,45));draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
for i,(label,path) in enumerate(items):
 im=Image.open(path).convert('RGB');im.thumbnail((390,455));x=(i%4)*400+(400-im.width)//2;y=(i//4)*500+38;sheet.paste(im,(x,y));draw.text(((i%4)*400+12,(i//4)*500+6),label,font=font,fill='white')
sheet.save(R/'reports/preview_sheet.png')
print('PREVIEW_SHEET_READY',R.name)
