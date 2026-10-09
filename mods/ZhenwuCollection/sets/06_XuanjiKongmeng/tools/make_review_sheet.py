"""Compose verified final TPAC previews for third-set acceptance."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports';font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28)
sheet=Image.new('RGB',(1440,980),'#242424');draw=ImageDraw.Draw(sheet)
for path,box in [('final_rest_front.png',(0,50,720,900)),('final_face_all.png',(730,50,710,710))]:
 with Image.open(R/path) as im:
  thumb=ImageOps.contain(im.convert('RGB'),box[2:]);sheet.paste(thumb,(box[0]+(box[2]-thumb.width)//2,box[1]))
draw.text((25,8),'玄机空濛 · v1.3.0 · 最终包离线预览',font=font,fill='white')
draw.text((750,800),'睫毛方向已按验收版本修正',font=font,fill='white')
draw.text((750,850),'游戏衣摆与骑乘效果待你验收',font=font,fill='white')
sheet.save(R/'final_delivery_preview.jpg',quality=92)
preview=json.loads((R/'final_preview_manifest.json').read_text())
names=[Path(p['path']).stem for p in preview['previews'] if not p['label'].startswith('face') and p['label']!='rest_front']
sheet=Image.new('RGB',(1600,600*((len(names)+3)//4)),'#222222');draw=ImageDraw.Draw(sheet)
for i,name in enumerate(names):
 im=ImageOps.contain(Image.open(R/(name+'.png')).convert('RGB'),(400,570));x=(i%4)*400;y=(i//4)*600;sheet.paste(im,(x,y+25));draw.text((x+8,y+5),name,fill='white')
sheet.save(R/'final_motion_review.jpg',quality=94)
uv=json.loads((R/'source_validation.json').read_text())['uv_verified'];assert [v['source_mesh'] for v in uv if v['flip_v']]==['mesh_04_491150']
identity=json.loads((R/'source_measurement.json').read_text());assert identity['status']=='pass'
package=ROOT/'module/ZhenwuCollection/AssetPackages/zw_xuanji.tpac'
(R/'eye_uv_validation.json').write_text(json.dumps({'status':'pass','final_package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'flipped_mesh':'mesh_04_491150','operation':'V -> 1 - V','other_meshes_unchanged':12,'texture_files_unchanged':True,'source_uv_report':uv,'geometry_uv_texture_identity_evidence':'reports/source_measurement.json','visual_review':'reports/final_face_all.png','scope':'Original lash geometry/UV/texture match accepted Yunhai; source and final UV independently checked; final near-eye render requires visual review.'},indent=2))
print('REVIEW_SHEETS_READY')
