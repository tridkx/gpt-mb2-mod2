"""Model-specific material and cloth decisions measured from supplied PMX files."""
from pathlib import Path
import json,sys
S=Path(__file__).resolve().parents[1];W=next(p for p in S.parents if (p/'tools/asset_helpers').is_dir());sys.path.insert(0,str(W/'tools/pmx_race_pipeline'))
from prepare import prepare
from references import prepare_references
# material: (attachment source height, native attachment bone, maximum travel)
PLAN={
 'JinhsiRace':{19:(18.8,13,.06),24:(8.16,13,.045),22:(11.62,0,.035),23:(10.9,0,.04)},
 'JinhsiOutfitRace':{10:(18.8,13,.06),40:(14.9,0,.035),41:(12.28,0,.045),42:(15.6,0,.04)},
 'BaizhiRace':{19:(18.5,13,.065)},
 'JianxinRace':{6:(18.8,13,.06),9:(15.81,13,.04),16:(13.4,0,.045),17:(12.73,0,.035)},
 'YinlinRace':{7:(21.8,13,.065)},
 'ShorekeeperRace':{23:(18.5,13,.04),30:(19.0,13,.04),31:(19.0,13,.04),1:(14.8,0,.035)},
 'ChangliRace':{9:(20.0,13,.06),31:(7.02,0,.035)},
 'ZhezhiRace':{7:(19.4,13,.055)}
}
EXCLUDE={'JinhsiRace':[26,27,28,29],'JinhsiOutfitRace':[31,32,33,45,46],'BaizhiRace':[27,28,29,30],'JianxinRace':[],'YinlinRace':[],'ShorekeeperRace':[34,35,36,37],'ChangliRace':[33],'ZhezhiRace':[]}
HEAD={'JinhsiRace':list(range(8,20))+[0,2,3,4,24],'JinhsiOutfitRace':[0,1,2,10,11,12,13]+list(range(16,31)),'BaizhiRace':list(range(9,20))+[0,24],'JianxinRace':[2,3,4,5,6,7,9,10],'YinlinRace':[0,4,5,6,7],'ShorekeeperRace':list(range(8,24))+[30,31,32,33],'ChangliRace':list(range(13))+[24],'ZhezhiRace':[0,3,4,5,6,7]}
def main():
 for row in json.loads((S/'batch_inventory.json').read_text(encoding='utf8'))['characters']:
  r=S/row['id'];p=r/'tools/model_config.json';c=json.loads(p.read_text(encoding='utf8'));inv=json.loads((r/'reports/source_inventory.json').read_text(encoding='utf8'));plan=PLAN[c['id']]
  c.update(head_materials=HEAD[c['id']],exclude_materials=EXCLUDE[c['id']],glass_materials=[6] if c['id']=='ZhezhiRace' else [],cloth_enabled=True,cloth_mode='direct',cloth_lods=[0,1,2,3],cloth_materials=list(plan),cloth_proxy_materials=list(plan),cloth_proxy_policy={'pin_band_m':.012,'minimum_component_height_m':.04,'max_proxy_vertices':4500},direct_diagnostic_lods=[0],hair_reference_body_blend_max=.55,weight_refinement={'shoulders':True,'waist':True,'crotch':True},shoulder_style='arm_only')
  c['cloth_parts']={str(i):{'fixed_above_source_y':y,'attachment_bone':bone,'max_distance_m':travel,'travel_slope':.22} for i,(y,bone,travel) in plan.items()}
  c['exclude_materials']+= {'JinhsiRace':[10],'JinhsiOutfitRace':[18,19,20],'BaizhiRace':[11],'ShorekeeperRace':[10,11]}.get(c['id'],[])
  c['skinned_skirt_materials']={'JinhsiRace':[20,21],'JinhsiOutfitRace':[34,35,36,37,39,43,44],'JianxinRace':[12,14,15,18],'ShorekeeperRace':[24,25,26,27,28,38],'ChangliRace':[18,26,27]}.get(c['id'],[])
  c['shoulder_style']='field'
  c['shoulder_materials']=[m['index'] for m in inv['materials'] if m['index'] not in HEAD[c['id']] and m['index'] not in plan]
  c['weight_smoothing_materials']={'JinhsiOutfitRace':[5,6,8],'BaizhiRace':[5,25],'JianxinRace':[0,1],'YinlinRace':[8,9,10,13],'ShorekeeperRace':[0],'ChangliRace':[13,14,22],'ZhezhiRace':[1,9,11,12,13,14]}.get(c['id'],[])
  c['weight_smoothing_iterations']=16
  c['consistent_cloth_attachment']=True
  c['minimum_ratios']={f"m{i:02d}":.75 for i in HEAD[c['id']] if i not in plan}
  c['rigid_material_bindings']={str(i):13 for i in HEAD[c['id']] if i not in plan}
  if c['id']=='BaizhiRace':c['rigid_material_bindings']['8']=11
  if c['id']=='JinhsiOutfitRace':c['rigid_material_bindings'].update({'3':11,'4':11})
  if c['id']=='ZhezhiRace':
   c['rigid_material_bindings']['2']=13;c['skinned_skirt_materials']=[11,12,13,14]
  c['hair_decision']='长发及明确独立的长饰品采用有限直接布料；短发、刘海、裙子、袖子普通蒙皮。各材质与挂点见 cloth_parts。'
  c['cloth_policy']={'skirt':False,'sleeves':False,'default':False,'enabled_materials':{str(i):next(m['name'] for m in inv['materials'] if m['index']==i) for i in plan}}
  p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8');prepare(r);prepare_references(r)
if __name__=='__main__':main()
