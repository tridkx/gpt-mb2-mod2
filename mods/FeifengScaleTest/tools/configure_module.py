import json
from pathlib import Path
import xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];M=R/'module/FeifengScaleTest'
plan=json.loads((R/'reports/scale_plan.json').read_text())
code='using TaleWorlds.Library;\nnamespace FeifengScaleTest { internal static class Profiles {\n'
for name,scales in [('Neutral',[[1]*3]*28)]+list(plan['profiles'].items()):
 code+='internal static readonly Vec3[] '+name+' = new Vec3[] {'+','.join('new Vec3('+','.join(format(x,'.9g')+'f' for x in row)+')' for row in scales)+'};\n'
code+='}}\n';(R/'tools/Runtime/Profiles.cs').write_text(code)
module=E.Element('Module')
for tag,value in [('Name','Feifeng Skeleton Scale Test'),('Id','FeifengScaleTest'),('Version','v0.1.3'),('DefaultModule','false'),('ModuleCategory','Singleplayer'),('Official','false'),('ModuleType','Community')]:E.SubElement(module,tag,value=value)
deps=E.SubElement(module,'DependedModules')
for id in ['Native','SandBoxCore','Sandbox']:E.SubElement(deps,'DependedModule',Id=id)
sub=E.SubElement(E.SubElement(module,'SubModules'),'SubModule')
for tag,value in [('Name','Feifeng Scale Probe'),('DLLName','FeifengScaleTest.dll'),('SubModuleClassType','FeifengScaleTest.SubModule')]:E.SubElement(sub,tag,value=value)
tags=E.SubElement(sub,'Tags');E.SubElement(tags,'Tag',key='DedicatedServerType',value='none');E.SubElement(tags,'Tag',key='IsNoRenderModeElement',value='false')
xml=E.SubElement(E.SubElement(module,'Xmls'),'XmlNode');E.SubElement(xml,'XmlName',id='Items',path='items');types=E.SubElement(xml,'IncludedGameTypes')
for type in ['Campaign','CampaignStoryMode','CustomGame']:E.SubElement(types,'GameType',value=type)
E.indent(module);E.ElementTree(module).write(M/'SubModule.xml',encoding='utf-8',xml_declaration=True)
items=E.Element('Items')
for profile in ['A','B','C','D','E','F']:
 for part,kind,title in [('head','HeadArmor','头部'),('body','BodyArmor','衣裙与手部'),('legs','LegArmor','腿部与鞋')]:
  id=f'ffs_{profile}_{part}';mesh=f'ffs_{"a" if profile in "CDEF" else profile.lower()}_{part}'
  label={'C':'单骨C一次','D':'单骨D持续','E':'矩阵E一次','F':'矩阵F持续'}.get(profile,'测试'+profile)
  item=E.SubElement(items,'Item',id=id,name=f'飞凤苗银{label} · {title}',mesh=mesh,culture='Culture.empire',weight='0.5',appearance='2',value='100',Type=kind,is_merchandise='true')
  attributes=dict(has_gender_variations='false',modifier_group='cloth_unarmoured',material_type='Cloth')
  if part=='head':attributes.update(head_armor='1',covers_head='true',hair_cover_type='all',beard_cover_type='all')
  elif part=='body':attributes.update(body_armor='1',arm_armor='1',leg_armor='1',covers_body='true',covers_hands='true')
  else:attributes.update(leg_armor='1',covers_legs='true')
  E.SubElement(E.SubElement(item,'ItemComponent'),'Armor',**attributes);E.SubElement(item,'Flags',Civilian='true',UseTeamColor='false')
E.indent(items);E.ElementTree(items).write(M/'ModuleData/items.xml',encoding='utf-8',xml_declaration=True)
print('MODULE_CONFIGURED')
