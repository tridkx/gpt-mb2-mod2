"""Record current runtime contract and retain superseded feedback evidence."""
from pathlib import Path
import json,shutil,subprocess,hashlib
from context import SERIES,workspace_root
w=workspace_root(SERIES);history=SERIES/'reports/history';history.mkdir(exist_ok=True)
for name in ['game_acceptance.json','delivery_validation.json','collection_installation.json','hair_proxy_visibility_fix.json']:
    p=SERIES/'reports'/name
    if p.exists():
        dest=history/('v0.1.1_'+name)
        if not dest.exists():shutil.copy2(p,dest)
        if name=='hair_proxy_visibility_fix.json':p.unlink()
p=Path(__file__).parent/'collection.py';text=p.read_text(encoding='utf8').replace("VERSION='v0.1.1'","VERSION='v0.1.2'").replace("arguments+=['-PreviousVersion','v0.1.0']","arguments+=['-PreviousVersion','v0.1.1']");p.write_text(text,encoding='utf8')
native=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/EmAssetPackages/armor555/armor555.tpac')
result=subprocess.run(['dotnet',str(w/'tools/AssetTool/AssetTool.dll'),'inspect',str(native),'clo_empire_legion_a'],capture_output=True,text=True,encoding='utf8',check=True)
reference={'source_package':str(native),'source_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'asset':'clo_empire_legion_a','metadata':json.loads(result.stdout)}
(SERIES/'reports/native_driver_reference.json').write_text(json.dumps(reference,indent=2))
result=subprocess.run(['dotnet',str(SERIES/'build/runtime_resource_patch/RuntimeResourcePatch.dll'),'check-bc-texture'],capture_output=True,text=True,check=True)
(SERIES/'reports/d3d11_bc_resource_test.json').write_text(json.dumps({'device':'Direct3D 11 WARP','game_started':False,'results':json.loads(result.stdout)},indent=2))
image=Path('C:/Users/DKX/Videos/Captures/Mount and Blade II Bannerlord.png');shutil.copy2(image,SERIES/'reports/user_feedback_v0.1.1.png')
(SERIES/'reports/user_feedback_v0.1.1.json').write_text(json.dumps({'date':'2026-10-15','version':'v0.1.1','character_creation':'Default lisa and amber leave the previous character displayed.','hair':'User screenshot shows Weisina hair patches persist after alpha-only proxy material repair.','screenshot':'reports/user_feedback_v0.1.1.png','screenshot_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'status':'previous_hair_fix_not_accepted'},indent=2))
entry='''## v0.1.2 — 2026-10-15

- 将不符合 Direct3D BC 顶层尺寸要求的 1181×1181 表情贴图从源 PNG 重编为 2048×2048；原 PNG 和全部网格／UV 保留。
- 含长发布料时按 Native 引用驱动网格：代理无直接可见布料标记和身体绑定，清除三个附加开关，保留可见头发的布料标记、碰撞与全部预处理／映射数据。
- 最终资源、GPU 资源创建和代理输入回读通过；创建页面及头发实机表现待用户复测。v0.1.1 的透明材质方案未通过用户实测，保留在历史报告。

'''
for p in SERIES.glob('*/reports/runtime_resource_fix.json'):
    root=p.parent.parent;log=root/'CHANGELOG.md';text=log.read_text(encoding='utf8');fix=json.loads(p.read_text());own=entry
    if not fix['texture_dimensions_fixed']:own='\n'.join(line for line in own.split('\n') if not line.startswith('- 将不符合'))
    if not fix['native_driver_role']:own='\n'.join(line for line in own.split('\n') if not line.startswith('- 含长发布料'))
    if '## v0.1.2' in text:
        begin=text.index('## v0.1.2');end=text.find('\n## ',begin+3);text=text[:begin]+own+('' if end<0 else text[end:].lstrip('\n'))
        log.write_text(text,encoding='utf8')
    else:log.write_text(text.replace('# 更新日志\n\n','# 更新日志\n\n'+own,1),encoding='utf8')
log=SERIES/'CHANGELOG.md';text=log.read_text(encoding='utf8')
if '## v0.1.2' not in text:log.write_text(text.replace('# 更新日志\n\n','# 更新日志\n\n'+entry,1),encoding='utf8')
readme=SERIES/'README.md';text=readme.read_text(encoding='utf8');needle='长发布料代理使用独立全透明裁切材质' if '长发布料代理使用独立全透明裁切材质' in text else '当前版本 v0.1.2 将可见头发与模拟驱动分开注册';start=text.index(needle);end=text.index('\n\n',start)
note='当前版本 v0.1.2 将可见头发与模拟驱动分开注册：代理仅由 `ClothMetamesh` 引用，没有直接可见布料标记、身体绑定或附加开关；可见头发继续启用布料。可见映射端同样只保留 Native 的 uses_cloth_simulation 标记，清除附加开关，布料数据保留。透明材质作为防护，不能作为实机未绘制代理的证据。[运行资源检查](reports/runtime_resource_fix.json)与 [Native 对照](reports/native_driver_reference.json)记录当前字段。默认丽莎、安柏和诺艾尔的表情贴图已按源 PNG 重编为合法 BC 尺寸，模型及 UV 不变；[本机 D3D11 对照](reports/d3d11_bc_resource_test.json)记录旧尺寸失败、新尺寸成功。创建页面和头发实机效果仍待复测。'
readme.write_text(text[:start]+note+text[end:],encoding='utf8')
print('RUNTIME_DOCS_READY')
