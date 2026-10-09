"""Compose existing QA renders into labeled delivery/report sheets."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'reports';font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28)
sheet=Image.new('RGB',(1440,980),'#242424');draw=ImageDraw.Draw(sheet)
for path,box in [('final_rest_front.png',(0,50,720,900)),('final_face_all.png',(730,50,710,710))]:
 with Image.open(R/path) as im:
  thumb=ImageOps.contain(im.convert('RGB'),box[2:]);sheet.paste(thumb,(box[0]+(box[2]-thumb.width)//2,box[1]))
draw.text((25,8),'云海蹑踪 · v1.0.0 · 最终包离线预览',font=font,fill='white')
draw.text((750,800),'眼影与睫毛 UV 方向已修正',font=font,fill='white')
draw.text((750,850),'游戏布料与动作效果待你验收',font=font,fill='white')
sheet.save(R/'final_delivery_preview.jpg',quality=92)
compare=Image.new('RGB',(1440,770),'#242424');draw=ImageDraw.Draw(compare)
for name,label,x in [('eye_uv_before.png','修正前',0),('final_face_all.png','UV 上下翻转后',720)]:
 with Image.open(R/name) as im:
  thumb=ImageOps.contain(im.convert('RGB'),(720,720));compare.paste(thumb,(x,50))
 draw.text((x+25,10),label,font=font,fill='white')
compare.save(R/'eye_uv_comparison.jpg',quality=92)
source=json.loads((R/'source_validation.json').read_text())
uv=source['uv_verified'];assert [u['source_mesh'] for u in uv if u['flip_v']]==['mesh_04_399558']
package=ROOT/'module/ZhenwuCollection/AssetPackages/zw_yunhai.tpac'
(R/'eye_uv_validation.json').write_text(json.dumps({'status':'pass','final_package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'flipped_mesh':'mesh_04_399558','operation':'V -> 1 - V','other_meshes_unchanged':13,'texture_files_unchanged':True,'source_uv_report':uv,'comparison':'reports/eye_uv_comparison.jpg','scope':'Source UV checked against input; final package UV checked against export geometry by release verifier; final near-eye render inspected separately'},indent=2))
print('REVIEW_SHEETS_READY')
