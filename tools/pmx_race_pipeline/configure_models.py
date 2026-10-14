"""Persist this batch's measured scale, hair and glass decisions per character."""
from pathlib import Path
import json
from context import SERIES
PLAN={
 'GanyuRace':([10],[10],'发_0_1',.2,.065,'后部单束长发超过肩背，启用有限摆动；刘海固定'),
 'NingguangOrchidRace':([11],[11],'右后髪_0_1',.2,.065,'两束长发延伸至腿部，启用有限摆动；前部发型固定'),
 'YunJinRace':([12],[12],'右辫_0_1',None,.055,'后部两条长辫独立下垂，启用有限摆动；帽与短发固定'),
 'KokomiRace':([15],[15],'右后髪_0_1',None,.075,'后部双长发下垂且与身体有间隙，启用有限摆动'),
 'XianyunRace':([11],[11],None,.55,.065,'后部高马尾较长，启用有限摆动；额前短发与发饰固定'),
 'NilouRace':([12,13],[12],'右HF_0_1',None,.06,'后部两束长发启用有限摆动，发绳随相同驱动跟随'),
 'AmberRace':([5],[5],None,.15,.055,'后部长发超过肩背，启用有限摆动；额前头发固定'),
 'KeqingOpulentRace':([12,22],[12],'右辫髮_0_1',None,.065,'双马尾启用有限摆动，发带跟随同一驱动；前部头发固定'),
 'YaeMikoRace':([9],[9],'后髪_0_1',.2,.075,'后部宽长发超过腰部，启用有限摆动；前发与饰物固定'),
 'AyakaRace':([0],[0],'髮_0_1',.3,.065,'后部长马尾启用有限摆动；刘海与头饰固定'),
 'HuTaoLanternRace':([15],[15],'左後发_1',.2,.065,'背部两束长发启用有限摆动，前发、帽与围巾固定'),
 'HuTaoRace':([10],[10],'右后发3_0_1',.2,.065,'后部双长发启用有限摆动，帽与前发固定'),
 'WeisinaRace':([15],[15],'髮_1',0,.055,'后部卷曲长发启用较小摆动范围，前发与翅膀固定')}
SHORT={
 'LisaLeafShadeRace':'发型较短且贴近肩颈，普通头部蒙皮更稳定',
 'LisaRace':'侧束较短、造型较紧，保留普通头部蒙皮',
 'AyakaSpringBloomRace':'当前服装为短发，保留普通头部蒙皮',
 'LumineRace':'短发，保留普通头部蒙皮',
 'SucroseRace':'短发，保留普通头部蒙皮',
 'FurinaRace':'随机选中的荒配色为短发，保留普通头部蒙皮',
 'JeanSeaBreezeRace':'高扎马尾较短、末端在肩部附近，保留普通头部蒙皮',
 'NoelleRace':'短发，保留普通头部蒙皮'}
GLASS={'HuTaoLanternRace':[32]}

def main():
    batch=json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'));decisions=[]
    for row in batch['characters']:
        root=Path(row['root']);path=root/'tools/model_config.json';c=json.loads(path.read_text(encoding='utf8'));r=json.loads((root/'reports/source_inventory.json').read_text(encoding='utf8'));bones={b['name']:b['position'] for b in r['source_bones']};head=bones['頭']
        if row['id'] in ['AmberRace','LisaRace','NoelleRace']:
            c['unit_scale']=.09;c['unit_scale_reason']='Older source family uses smaller model units; uniform 0.09 conversion aligns anatomical head heights with the supplied models. No proportional reshaping.'
        if row['id']=='KeqingOpulentRace':c['exclude_materials']=[11]
        if row['id']=='WeisinaRace':c['rigid_material_bindings']={'29':11,'30':11}
        if row['id']=='NingguangOrchidRace':c['arm_material_bindings']=[30]
        if row['id']=='KeqingOpulentRace':c['arm_material_bindings']=[14]
        if row['id']=='YunJinRace':c['rigid_material_bindings']={'26':11}
        if row['id']=='XianyunRace':c['rigid_material_bindings']={'25':11}
        if row['id']=='XianyunRace':c['arm_material_bindings']=[16]
        if row['id']=='WeisinaRace':c['arm_material_bindings']=[19,21]
        if row['id']=='HuTaoLanternRace':c['rigid_material_bindings']={'29':11,'30':11}
        if row['id']=='JeanSeaBreezeRace':c['rigid_material_bindings']={'13':0,'14':0,'15':0,'18':0}
        if row['id']=='AyakaRace':c['rigid_material_bindings']={'12':0}
        if row['id']=='WeisinaRace':c['crotch_outer_width_multiplier']=3.0;c['crotch_depth_m']=.28;c['crotch_lateral_transition_multiplier']=2.0
        c['glass_materials']=GLASS.get(row['id'],[])
        c['head_materials']=[m['index'] for m in r['materials'] if any(t in m['name'] for t in ['髮','髪','头发','眉','睫','面','颜','脸','目','眼','口','齿','齒','牙','舌','帽','头饰','髮饰','发饰']) and not any(t in m['name'] for t in ['神之眼','眼镜','肌'])]
        c['head_materials']=sorted(set(c['head_materials']+c['glass_materials']))
        c['weight_refinement']={'shoulders':True,'crotch':True,'waist':True}
        c['shoulder_style']='field_narrow' if row['id'] in ['NingguangOrchidRace','XianyunRace','KeqingOpulentRace'] else 'field' if row['id'] in ['YunJinRace','AyakaRace'] else 'arm_only'
        if row['id']=='AmberRace':c['shoulder_style']='field'
        c['shoulder_materials']=[m['index'] for m in r['materials'] if any(t in m['name'] for t in ['体','服','肌','皮肤','手','臂','材质']) and not any(t in m['name'] for t in ['饰','手环','手飾'])]
        if row['id'] in PLAN:
            mats,proxy_mats,bone,zmin,travel,reason=PLAN[row['id']];anchor=bones[bone][1] if bone else head[1]+.5
            c.update(cloth_enabled=True,cloth_lods=[0,1,2,3],cloth_materials=mats,cloth_proxy_materials=proxy_mats,hair_decision=reason,cloth_parts={str(i):{'fixed_above_source_y':anchor,'source_z_min':zmin,'max_distance_m':travel,'travel_slope':.3} for i in mats})
            c['cloth_proxy_policy']={'pin_band_m':.015,'minimum_component_height_m':.055,'max_proxy_vertices':4500}
            c['hair_reference_body_blend_max']=.7
        else:c.update(cloth_enabled=False,cloth_lods=[],cloth_materials=[],cloth_parts={},hair_decision=SHORT[row['id']])
        # Protect the fixed face and eye outlines in all distant render LODs.
        c['minimum_ratios']={f"m{m['index']:02d}":.7 for m in r['materials'] if any(t in m['name'] for t in ['面','颜','脸','眉','睫','白目','眼睛','眼白','目光'])}
        path.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8');decisions.append({'id':c['id'],'name':c['display_name'],'unit_scale':c['unit_scale'],'hair_cloth':c['cloth_enabled'],'hair_decision':c['hair_decision'],'hair_materials':c['cloth_materials'],'ignored_models':c['ignored_models'],'source_model':c['source_model']})
    (SERIES/'hair_decisions.json').write_text(json.dumps({'date':'2026-10-14','decisions':decisions},ensure_ascii=False,indent=2),encoding='utf8');print('MODEL_DECISIONS',len(decisions),'hair cloth',sum(d['hair_cloth'] for d in decisions))

if __name__=='__main__':main()
