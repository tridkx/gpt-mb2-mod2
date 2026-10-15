"""Generate new troop definitions from this machine's native T5 data; never edit the dependency."""
import argparse
import copy
from collections import Counter
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CLANS = ['looters', 'sea_raiders', 'mountain_bandits', 'forest_bandits', 'steppe_bandits', 'desert_bandits']
# race, role, donor T5 troop, four weapon slots (None means empty).
PLAN = [
 ('noelle','shield','imperial_legionary',['vlandia_mace_2_t4','heavy_heater_shield','western_spear_4_t4']),
 ('jean_seabreeze','shield','imperial_legionary',['sturgia_sword_4_t4','sturgia_infantry_shield_a','imperial_throwing_spear_1_t4']),
 ('furina','shield','imperial_legionary',['empire_sword_5_t4','southern_oval_shield','eastern_javelin_2_t3']),
 ('lumine','shock','battanian_veteran_falxman',['sturgia_mace_2_t4','sturgia_sword_5_t4','northern_throwing_axe_1_t1']),
 ('ayaka','shock','battanian_veteran_falxman',['battania_2hsword_4_t4','woodland_throwing_axe_1_t1','woodland_throwing_axe_1_t1']),
 ('ayaka_springbloom','shock','battanian_veteran_falxman',['battania_2hsword_4_t4','vlandia_sword_4_t4','woodland_throwing_axe_1_t1']),
 ('hutao','polearm','aserai_veteran_infantry',['vlandia_polearm_1_t5','vlandia_sword_2_t3','western_throwing_axe_1_t1']),
 ('hutao_lantern','polearm','aserai_veteran_infantry',['eastern_spear_4_t4','aserai_sword_4_t4','southern_oval_shield','eastern_javelin_2_t3']),
 ('emilie','polearm','aserai_veteran_infantry',['vlandia_pike_1_t5','vlandia_sword_4_t4']),
 ('ganyu','archer','imperial_palatine_guard',['steppe_war_bow','bodkin_arrows_b','bodkin_arrows_b','empire_sword_3_t3']),
 ('amber','archer','imperial_palatine_guard',['composite_steppe_bow','steppe_arrows','steppe_arrows','khuzait_sword_3_t3']),
 ('sucrose','archer','imperial_palatine_guard',['steppe_war_bow','piercing_arrows','piercing_arrows','aserai_sword_3_t3']),
 ('kokomi','archer','imperial_palatine_guard',['composite_steppe_bow','bodkin_arrows_b','bodkin_arrows_b','aserai_sword_4_t4']),
 ('lisa','crossbow','vlandian_sharpshooter',['crossbow_d','bolt_d','empire_mace_2_t4','reinforced_kite_shield']),
 ('lisa_leafshade','crossbow','vlandian_sharpshooter',['crossbow_f','bolt_c','empire_mace_3_t4','southern_oval_shield']),
 ('yaemiko','crossbow','vlandian_sharpshooter',['crossbow_d','bolt_d','empire_sword_5_t4','sturgia_infantry_shield_a']),
 ('nilou','horse_archer','khuzait_heavy_horse_archer',['composite_steppe_bow','steppe_arrows','steppe_arrows','khuzait_sword_4_t4']),
 ('xianyun','horse_archer','khuzait_heavy_horse_archer',['steppe_war_bow','bodkin_arrows_b','bodkin_arrows_b','empire_sword_3_t3']),
 ('weisina','horse_archer','khuzait_heavy_horse_archer',['composite_steppe_bow','piercing_arrows','piercing_arrows','aserai_sword_3_t3']),
 ('yunjin','cavalry','vlandian_vanguard',['vlandia_lance_2_t4','wide_heater_shield','vlandia_sword_4_t4']),
 ('keqing_opulent','cavalry','khuzait_heavy_lancer',['khuzait_lance_2_t4','steppe_guardian_shield','khuzait_sword_4_t4']),
 ('ningguang_orchid','cavalry','imperial_cataphract',['empire_lance_2_t4','heavy_horsemans_kite_shield','empire_sword_5_t4']),
]
ROLE_ZH = dict(shield='盾步兵',shock='双手突击兵',polearm='长杆步兵',archer='弓箭手',crossbow='弩手',horse_archer='骑射兵',cavalry='近战骑兵')
ROLE_WEIGHTS = {clan: dict(Counter(row[1] for row in PLAN)) for clan in CLANS}

def write_xml(path, root):
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space='  ')
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root',type=Path,default=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord'))
    parser.add_argument('--race-source',type=Path,help='GenshinRaceCollection module directory; defaults to workspace source, then installed module')
    args=parser.parse_args()
    game=args.game_root
    native=game/'Modules/SandBoxCore/ModuleData'
    troops={x.get('id'):x for p in [native/'spnpccharacters.xml',game/'Modules/SandBox/ModuleData/bandits.xml']
            for x in ET.parse(p).getroot() if x.get('id')}
    items={x.get('id'):x for p in sorted((native/'items').glob('*.xml')) for x in ET.parse(p).getroot() if x.get('id')}
    templates={x.get('id'):x for x in ET.parse(game/'Modules/SandBox/ModuleData/partyTemplates.xml').getroot()}
    clans={x.get('id'):x for x in ET.parse(game/'Modules/SandBox/ModuleData/spclans.xml').getroot() if x.get('is_bandit')=='true'}
    cultures={x.get('id'):x for x in ET.parse(native/'spcultures.xml').getroot()}
    candidates=[p/'mods/GenshinRaceCollection/module/GenshinRaceCollection' for p in ROOT.parents]
    dependency=args.race_source or next((p for p in candidates if (p/'SubModule.xml').is_file()),game/'Modules/GenshinRaceCollection')
    test_troops={x.get('race'):x for x in ET.parse(dependency/'ModuleData/test_troop.xml').getroot()}
    translations={x.get('id'):x.get('text') for module in ['Native','SandBoxCore','SandBox']
                  for p in (game/'Modules'/module/'ModuleData/Languages/CNs').glob('*.xml')
                  for x in ET.parse(p).getroot().iter('string')}
    def name(node):
        text=node.get('name','')
        if text.startswith('{='):
            key,text=text[2:].split('}',1)
            return translations.get(key,text)
        return text
    out=ROOT/'module/GenshinBanditRace/ModuleData'
    npc_root=ET.Element('NPCCharacters')
    armor_root=ET.Element('TroopArmor',schemaVersion='1')
    catalog=ET.Element('BanditCatalog',schemaVersion='1')
    rows=[]
    signatures=set()
    for race,role,donor_id,weapons in PLAN:
        assert donor_id in troops and troops[donor_id].get('level')=='26',donor_id
        assert race in test_troops,race
        donor=troops[donor_id]
        common={e.get('slot'):e.get('id').removeprefix('Item.') for e in donor.findall('Equipments/equipment')}
        mount={k:v for k,v in common.items() if k in ['Horse','HorseHarness']} if role in ['cavalry','horse_archer'] else {}
        if role in ['cavalry','horse_archer']: assert set(mount)=={'Horse','HorseHarness'},donor_id
        slots={f'Item{i}':v for i,v in enumerate(weapons) if v}
        slots.update(mount)
        assert all(x in items for x in slots.values()), slots
        signature=tuple(sorted(slots.items()))
        assert signature not in signatures, race
        signatures.add(signature)
        armor_totals=[]; weights=[]
        for roster in donor.findall('Equipments/EquipmentRoster'):
            if roster.get('civilian')=='true' or roster.get('equipmentType')=='Civilian': continue
            equipment={e.get('slot'):e.get('id').removeprefix('Item.') for e in roster.findall('equipment')}
            equipment.update(common)
            total=[0,0,0,0]; weight=Decimal(0)
            for slot in ['Head','Body','Cape','Gloves','Leg']:
                if slot not in equipment: continue
                item=items[equipment[slot]]
                armor=item.find('ItemComponent/Armor')
                assert armor is not None,equipment[slot]
                total=[a+int(armor.get(k,'0')) for a,k in zip(total,['head_armor','body_armor','arm_armor','leg_armor'])]
                weight+=Decimal(item.get('weight'))
            armor_totals.append(total); weights.append(weight)
        assert armor_totals,donor_id
        armor=[int((sum(Decimal(t[i]) for t in armor_totals)/len(armor_totals)).quantize(Decimal('1'),rounding=ROUND_HALF_UP)) for i in range(4)]
        weight=sum(weights)/len(weights)
        troop_id='gbr_'+race
        display_name=name(test_troops[race])+'·'+ROLE_ZH[role]
        npc=ET.SubElement(npc_root,'NPCCharacter',id=troop_id,name=display_name,level='16',occupation='Bandit',culture='Culture.looters',
            race=race,is_female='true',age='25',face_mesh_cache='false',
            default_group='HorseArcher' if role=='horse_archer' else 'Cavalry' if role=='cavalry' else 'Ranged' if role in ['archer','crossbow'] else 'Infantry')
        face=ET.SubElement(npc,'face')
        for tag in ['BodyProperties','BodyPropertiesMax']:
            ET.SubElement(face,tag,version='4',age='25',weight='0.5',build='0.5',key='0'*128)
        npc.append(copy.deepcopy(donor.find('skills')))
        equipments=ET.SubElement(npc,'Equipments')
        roster=ET.SubElement(equipments,'EquipmentRoster')
        for slot,item_id in slots.items(): ET.SubElement(roster,'equipment',slot=slot,id='Item.'+item_id)
        ET.SubElement(equipments,'EquipmentRoster',civilian='true')
        ET.SubElement(armor_root,'Troop',id=troop_id,race=race,**dict(zip(['head','body','arms','legs'],map(str,armor))))
        ET.SubElement(catalog,'Troop',id=troop_id,race=race,role=role,weight=str(weight),fallback='looter')
        rows.append(dict(id=troop_id,race=race,name=display_name,role=role,donor=donor_id,donor_name=name(donor),
            skills={x.get('id'):int(x.get('value')) for x in donor.findall('skills/skill')},armor=armor,armor_weight=float(weight),
            equipment={slot:dict(id=item_id,name=name(items[item_id])) for slot,item_id in slots.items()}))
    coverage=[]
    for clan_id in CLANS:
        clan=clans[clan_id]; template_id=clan.get('default_party_template').removeprefix('PartyTemplate.')
        template=templates[template_id]
        native_ids={x.get('troop').removeprefix('NPCCharacter.') for x in template.findall('stacks/PartyTemplateStack')}
        # Include all native ordinary members of this culture, not just its first template stack.
        culture_id=clan.get('culture').removeprefix('Culture.')
        native_ids.update(x.get('id') for x in troops.values() if x.get('culture')=='Culture.'+culture_id and x.get('occupation')=='Bandit')
        native_ids.discard('deserter')
        assert native_ids and all(x in troops for x in native_ids),(clan_id,sorted(x for x in native_ids if x not in troops))
        c=ET.SubElement(catalog,'Clan',id=clan_id)
        for troop_id in sorted(native_ids): ET.SubElement(c,'Native',id=troop_id)
        for role,weight in ROLE_WEIGHTS[clan_id].items(): ET.SubElement(c,'Role',id=role,weight=str(weight))
        assert sum(ROLE_WEIGHTS[clan_id].values())==22
        coverage.append(dict(clan=clan_id,template=template_id,native_troops=sorted(native_ids),role_weights=ROLE_WEIGHTS[clan_id]))
    assert len(rows)==22 and {r['race'] for r in rows if r['role']=='cavalry'}=={'yunjin','keqing_opulent','ningguang_orchid'}
    write_xml(out/'troops.xml',npc_root); write_xml(out/'rtb_troop_armor.xml',armor_root); write_xml(out/'bandit_catalog.xml',catalog)
    report=dict(game_version=ET.parse(game/'Modules/Native/SubModule.xml').getroot().find('Version').get('value'),
                characters=rows,coverage=coverage,excluded=['deserters','hideout_boss_parties','quest_specific_parties','naval_parties'],
                source_hashes={str(p.relative_to(game)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                    [native/'spnpccharacters.xml',native/'spcultures.xml',game/'Modules/SandBox/ModuleData/bandits.xml',game/'Modules/SandBox/ModuleData/partyTemplates.xml',game/'Modules/SandBox/ModuleData/spclans.xml']})
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/troop_configuration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 原神土匪兵种装备与属性','', '所有兵种为 T3／Level 16；固有护甲与熟练度来自表中原版 T5，五个防具槽为空。', '',
           '| 兵种 | T5 基准 | 武器与盾牌 | 坐骑／马具 | 固有护甲（头／身／臂／腿） | 防具等效重量 |',
           '| --- | --- | --- | --- | --- | --- |']
    for row in rows:
        weapons='、'.join(v['name'] for k,v in row['equipment'].items() if k.startswith('Item'))
        mount='／'.join(v['name'] for k,v in row['equipment'].items() if k in ['Horse','HorseHarness']) or '无'
        lines.append(f"| {row['name']} | {row['donor_name']} | {weapons} | {mount} | {'／'.join(map(str,row['armor']))} | {row['armor_weight']:.2f} |")
    lines+=['','同名弹药或投掷武器重复出现，表示各占一个武器槽。武器、弹药、盾牌与马具真实重量独立计算；等效重量仅补防具，默认倍率为 1。',
            '', '完整技能、物品 ID、生成基准与六类覆盖明细见 [配置报告](../reports/troop_configuration.json)。',
            '', '六类土匪使用相同的完整22兵种池，每次等概率抽取一个角色，允许同队重复；没有地域、文化或定位权重差异。小队不保证同时出现全部22类，长期抽取概率各为1/22。']
    (ROOT/'docs').mkdir(exist_ok=True)
    (ROOT/'docs/troops.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('GENERATED 22 distinct T3 troops; cavalry = Yun Jin, Keqing, Ningguang; six bandit clans; deserters excluded')

if __name__=='__main__': main()
