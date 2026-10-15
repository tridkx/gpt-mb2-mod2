"""Generate only this module, using installed v1.4.8 data and the WW dependency."""
from pathlib import Path
import copy
import json
import xml.etree.ElementTree as E
from decimal import Decimal, ROUND_HALF_UP

ROOT = Path(__file__).resolve().parents[1]
GAME = Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord')
DEP = ROOT.parent/'WutheringWavesRaceCollection/module/WutheringWavesRaceCollection'
OUT = ROOT/'module/WutheringUndeadRace/ModuleData'
ROLES = ['Infantry','Ranged','Cavalry','HorseArcher']
PLAN = [
 ('jianxin','鉴心',0,1.35,1.10,200,100),
 ('changli','长离',0,.70,.45,240,220),
 ('zhezhi','折枝',1,.85,.75,240,150),
 ('yinlin','吟霖',1,1.10,1.,240,130),
 ('jinhsi','今汐',2,1.30,1.15,240,200),
 ('jinhsi_outfit','今汐·桃夭灼灼',2,.85,.70,250,220),
 ('baizhi','白芷',3,.65,.50,220,240),
 ('shorekeeper','守岸人',3,1.20,1.10,240,160),
]
DONORS = [
 ['imperial_recruit','imperial_infantryman','imperial_trained_infantryman','imperial_veteran_infantryman','imperial_legionary'],
 ['imperial_recruit','imperial_archer','imperial_trained_archer','imperial_veteran_archer','imperial_palatine_guard'],
 ['imperial_recruit','vlandian_squire','khuzait_horseman','khuzait_lancer','khuzait_heavy_lancer'],
 ['imperial_recruit','khuzait_tribal_warrior','khuzait_raider','khuzait_horse_archer','khuzait_heavy_horse_archer'],
]
WEAPONS = {
 'jianxin': [['peasant_hammer_1_t1','small_heater_shield'],['vlandia_mace_1_t2','old_kite_shield'],['morningstar_mace_t3','heavy_heater_shield'],['empire_mace_3_t4','pavise_shield'],['empire_mace_5_t5','pavise_shield']],
 'changli': [['battania_2hsword_1_t2'],['battania_2hsword_2_t3'],['battania_2hsword_4_t4','woodland_throwing_axe_1_t1'],['khuzait_polearm_1_t4','woodland_throwing_axe_1_t1','woodland_throwing_axe_1_t1'],['battania_2hsword_5_t5','woodland_throwing_axe_1_t1','woodland_throwing_axe_1_t1']],
 'zhezhi': [[b,a,'peasant_sickle_1_t1'] if j<2 else [b,a,a,'empire_sword_3_t3'] for j,(b,a) in enumerate(zip(['hunting_bow','lowland_longbow','woodland_longbow','noble_long_bow','noble_long_bow'],['range_arrows','barbed_arrows','piercing_arrows','bodkin_arrows_b','bodkin_arrows_b']))],
 'yinlin': [[b,a,'empire_mace_1_t2'] if j<2 else [b,a,a,'empire_mace_3_t4'] for j,(b,a) in enumerate(zip(['crossbow_a','crossbow_b','crossbow_c','crossbow_f','crossbow_f'],['bolt_a','bolt_b','bolt_c','bolt_d','bolt_d']))],
 'jinhsi': [['eastern_spear_1_t2','small_heater_shield','empire_sword_1_t2'],['vlandia_lance_1_t3','horsemans_heater_shield','empire_sword_1_t2'],['vlandia_lance_2_t4','heavy_horsemans_kite_shield','empire_sword_3_t3'],['vlandia_lance_3_t5','heavy_horsemans_kite_shield','empire_sword_5_t4'],['empire_lance_3_t5','heavy_horsemans_kite_shield','empire_sword_5_t4']],
 'jinhsi_outfit': [['khuzait_sword_1_t2'],['khuzait_sword_3_t3'],['khuzait_polearm_1_t4','khuzait_sword_3_t3'],['khuzait_polearm_1_t4','battania_2hsword_4_t4'],['khuzait_polearm_2_t5','battania_2hsword_5_t5']],
 'baizhi': [[b,a,a,'khuzait_sword_1_t2' if j<2 else 'khuzait_sword_4_t4'] for j,(b,a) in enumerate(zip(['hunting_bow','steppe_bow','composite_bow','noble_bow','noble_bow'],['range_arrows','steppe_arrows','steppe_arrows','piercing_arrows','piercing_arrows']))],
 'shorekeeper': [[b,a,a,'empire_mace_1_t2' if j<3 else 'empire_mace_3_t4'] for j,(b,a) in enumerate(zip(['hunting_bow','steppe_bow','composite_steppe_bow','steppe_war_bow','noble_bow'],['range_arrows','steppe_arrows','bodkin_arrows_a','bodkin_arrows_b','bodkin_arrows_b']))],
}

def write(path, root):
 E.indent(root,space='  ')
 E.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 data=GAME/'Modules/SandBoxCore/ModuleData'
 troops={x.get('id'):x for x in E.parse(data/'spnpccharacters.xml').getroot()}
 items={x.get('id'):x for p in (data/'items').glob('*.xml') for x in E.parse(p).getroot() if x.get('id')}
 assert all(w in items for sets in WEAPONS.values() for ws in sets for w in ws), sorted({w for sets in WEAPONS.values() for ws in sets for w in ws if w not in items})
 skins=E.Element('skins'); monsters=E.Element('Monsters'); actions=E.Element('action_sets')
 source_skins=E.parse(DEP/'ModuleData/skins.xml').getroot()
 source_monsters=E.parse(DEP/'ModuleData/monsters.xml').getroot()
 source_actions=E.parse(DEP/'ModuleData/action_sets.xml').getroot()
 npcs=E.Element('NPCCharacters'); custom_items=E.Element('Items'); catalog=E.Element('UndeadCatalog',schemaVersion='1')
 rows=[]
 def defense(donor):
  common={e.get('slot'):e.get('id').removeprefix('Item.') for e in donor.findall('Equipments/equipment')}
  armors=[];weights=[]
  for roster in donor.findall('Equipments/EquipmentRoster'):
   if roster.get('civilian')=='true' or roster.get('equipmentType')=='Civilian':continue
   eq={e.get('slot'):e.get('id').removeprefix('Item.') for e in roster.findall('equipment')};eq.update(common)
   a=[0]*4;w=Decimal(0)
   for slot in ['Head','Body','Cape','Gloves','Leg']:
    if slot not in eq:continue
    item=items[eq[slot]]; ar=item.find('ItemComponent/Armor')
    a=[v+int(ar.get(k,'0')) for v,k in zip(a,['head_armor','body_armor','arm_armor','leg_armor'])];w+=Decimal(item.get('weight'))
   armors.append(a);weights.append(w)
  return [sum(a[j] for a in armors)/len(armors) for j in range(4)],float(sum(weights)/len(weights)),common
 def weapon(base,key,tier,slot,lord):
  x=copy.deepcopy(items[base]); id=f'wur_{key}_{"lord" if lord else tier}_w{slot}'
  x.set('id',id);x.set('name',f'{next(p[1] for p in PLAN if p[0]==key)}·{"统领" if lord else str(tier)}·感染武装{slot+1}')
  x.set('is_merchandise','false')
  # Crafted weapons keep their physical design; T4/5 and lord variants grow visibly.
  factor=1.22 if lord else (1.10 if tier==5 else 1.04 if tier==4 else 1.)
  for piece in x.findall('Pieces/Piece'):
   piece.set('scale_factor',str(round(float(piece.get('scale_factor','100'))*factor)))
  for w in x.findall('ItemComponent/Weapon'):
   for attr in ['swing_damage','thrust_damage']:
    if w.get(attr):w.set(attr,str(round(float(w.get(attr))*(1.50 if lord else 1.25 if tier==5 else 1.10 if tier==4 else 1.))))
   if x.get('Type') in ['Arrows','Bolts']:
    w.set('stack_amount',str(55 if lord else 40 if tier==5 else 32 if tier==4 else int(w.get('stack_amount','24'))))
   if x.get('Type')=='Shield' and w.get('hit_points'):
    w.set('hit_points',str(round(float(w.get('hit_points'))*(2.5 if lord else 1.8 if tier==5 else 1.))))
   if key=='baizhi' and x.get('Type')=='Bow' and tier>=4:
    w.set('speed_rating',str(round(float(w.get('speed_rating','80'))*1.12)))
   if key in ['baizhi','shorekeeper'] and x.get('Type')=='Bow':
    flags=w.find('WeaponFlags')
    if flags is not None:flags.attrib.pop('CantReloadOnHorseback',None)
  if key in ['baizhi','shorekeeper']:
   for f in x.iter('WeaponFlags'):f.attrib.pop('CantReloadOnHorseback',None)
  custom_items.append(x);return id
 for key,zh,role,am,wm,primary,movement in PLAN:
  race='ww_'+key; lr='wur_lord_'+key
  r=copy.deepcopy(next(x for x in source_skins if x.get('id')==race));r.set('id',lr)
  for skin in r:
   skin.set('name',skin.get('name').replace(race,lr));skin.set('min_scale',str(float(skin.get('min_scale','1'))*1.5))
  skins.append(r)
  for m in source_monsters:
   if (m.get('id')==race or m.get('id','').startswith(race+'_')) and not (key=='jinhsi' and m.get('id','').startswith('ww_jinhsi_outfit')):
    n=copy.deepcopy(m)
    for k,v in n.attrib.items():
     if race in v:n.set(k,v.replace(race,lr))
    monsters.append(n)
  for a in source_actions:
   if race in a.get('name',a.get('id','')) and not (key=='jinhsi' and 'ww_jinhsi_outfit' in a.get('name',a.get('id',''))):
    n=copy.deepcopy(a)
    for k in ['name','id']:
     if n.get(k):n.set(k,n.get(k).replace(race,lr))
    # skeleton is deliberately shared with the original dependency.
    actions.append(n)
  for tier in range(1,7):
   lord=tier==6; t=min(5,tier); donor_id=DONORS[role][t-1];donor=troops[donor_id]
   armor,weight,common=defense(donor)
   ramp=(t-1)/4; af=1+(am-1)*ramp;wf=1+(wm-1)*ramp
   if lord:af*=1.6;wf*=1.1
   armor=[min(500,int(Decimal(str(v*af)).quantize(Decimal(1),rounding=ROUND_HALF_UP))) for v in armor]
   id='wur_'+key+('_lord_template' if lord else '_t'+str(t))
   display=zh+'·'+('感染统领' if lord else ['感染步兵','感染射手','感染骑兵','感染骑射'][role]+str(t))
   # A dynamic hero template is a CharacterObject, not a pre-existing hero.
   # HeroCreator creates the hero instance later, after the campaign is ready.
   npc=E.SubElement(npcs,'NPCCharacter',id=id,name=display,level=str(36 if lord else 1+5*t),occupation='Lord' if lord else 'Soldier',culture='Culture.empire',race=lr if lord else race,is_female='true',age='30',default_group=ROLES[role],face_mesh_cache='false',**({'is_template':'true'} if lord else {}))
   face=E.SubElement(npc,'face')
   for tag in ['BodyProperties','BodyPropertiesMax']:E.SubElement(face,tag,version='4',age='30',weight='0.5',build='0.5',key='0'*128)
   skills={s.get('id'):int(s.get('value')) for s in donor.findall('skills/skill')}
   target=round(20+(primary-20)*ramp);move=round(20+(movement-20)*ramp)
   if lord:target+=60;move+=30
   if key=='jianxin':skills['OneHanded']=target;skills['Athletics']=move
   elif key=='changli':skills['TwoHanded']=target;skills['Polearm']=target;skills['Athletics']=move;skills['Throwing']=round(target*.7)
   elif key in ['zhezhi','yinlin']:skills['Crossbow' if key=='yinlin' else 'Bow']=target;skills['Athletics']=move
   elif role==2:skills['Polearm']=target;skills['Riding']=move;skills['TwoHanded']=target if key=='jinhsi_outfit' else skills['TwoHanded'];skills['OneHanded']=round(target*.75)
   else:skills['Bow']=target;skills['Riding']=move;skills['OneHanded']=round(20+(70 if key=='shorekeeper' else 110)*ramp)
   sk=E.SubElement(npc,'skills')
   for k,v in skills.items():E.SubElement(sk,'skill',id=k,value=str(v))
   if not lord and t<5:E.SubElement(E.SubElement(npc,'upgrade_targets'),'upgrade_target',id='NPCCharacter.wur_'+key+'_t'+str(t+1))
   eq=E.SubElement(npc,'Equipments'); roster=E.SubElement(eq,'EquipmentRoster')
   slots={}
   for j,base in enumerate(WEAPONS[key][t-1]):slots['Item'+str(j)]=weapon(base,key,t,j,lord)
   if role>=2:
    horse=common.get('Horse','sumpter_horse');harness=common.get('HorseHarness','light_harness')
    if t==1:horse='sumpter_horse';harness='light_harness'
    assert horse in items and harness in items,(horse,harness)
    slots.update(Horse=horse,HorseHarness=harness)
   for slot,item in slots.items():E.SubElement(roster,'equipment',slot=slot,id='Item.'+item)
   civ=E.SubElement(eq,'EquipmentRoster',civilian='true')
   # Preserve a usable unarmoured civilian weapon; all five armour slots stay empty.
   E.SubElement(civ,'equipment',slot='Item0',id='Item.'+slots['Item'+str(len(WEAPONS[key][t-1])-1)])
   E.SubElement(catalog,'Troop',id=id,race=lr if lord else race,key=key,role=ROLES[role],tier=str(t),lord=str(lord).lower(),weight=f'{weight*wf:.6f}',head=str(armor[0]),body=str(armor[1]),arms=str(armor[2]),legs=str(armor[3]))
   rows.append(dict(id=id,key=key,name=display,race=lr if lord else race,role=ROLES[role],tier=t,lord=lord,donor=donor_id,armor=armor,weight=round(weight*wf,4),skills=skills,equipment=slots))
 for filename,node in [('troops.xml',npcs),('items.xml',custom_items),('skins.xml',skins),('monsters.xml',monsters),('action_sets.xml',actions),('undead_catalog.xml',catalog)]:write(OUT/filename,node)
 assert len(rows)==48 and len(skins)==8 and len(monsters)>=8 and len(actions)>0
 (ROOT/'reports/troop_configuration.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# 感染兵与统领数据','', '原版同阶防御为底，职业差分随T1—T5线性增加；统领使用本职业T5护甲的1.6倍。头／身／臂／腿为固有护甲，负重仅补防具。','', '| 角色兵种 | 原版防御基准 | 固有护甲 | 等效负重 | 武器槽 |','| --- | --- | --- | ---: | --- |']
 for row in rows:lines.append('| '+row['name']+' | '+row['donor']+' | '+'／'.join(map(str,row['armor']))+' | '+str(row['weight'])+' | '+'、'.join(WEAPONS[row['key']][row['tier']-1])+' |')
 (ROOT/'docs').mkdir(exist_ok=True);(ROOT/'docs/troops.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print('Generated 40 troops + 8 lord templates; shared dependency assets unchanged.')

if __name__=='__main__':main()
