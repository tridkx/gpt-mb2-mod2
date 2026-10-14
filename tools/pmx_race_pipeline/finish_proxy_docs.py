"""Record the targeted repair and keep current documentation coherent."""
import json,shutil
from pathlib import Path
from context import SERIES
collection_script=Path(__file__).parent/'collection.py'
collection_script.write_text(collection_script.read_text(encoding='utf8').replace("'date':'2026-10-14'","'date':'2026-10-15'"),encoding='utf8')
for path in SERIES.glob('*/reports/hair_proxy_visibility_fix.json'):
    root=path.parent.parent;images=list((root/'reports').glob('hair_proxy_after_*.png'));assert len(images)==4,root.name
    data={'status':'pass','package_sha256':json.loads(path.read_text())['final_package_sha256'],'scope':'Final exported TPAC geometry including cloth driver; fully clipped only after decoded texture alpha check','previews':[p.relative_to(root).as_posix() for p in images],'game_verified':False}
    (root/'reports/hair_proxy_visibility_preview.json').write_text(json.dumps(data,indent=2))
    log=root/'CHANGELOG.md';text=log.read_text(encoding='utf8');entry='''## v0.1.1 — 2026-10-15

- 模拟代理改用独立全透明裁切材质，避免借用脸部材质产生随头发移动的单色色块。
- 可见四级网格、原贴图、骨架、权重及布料预处理／映射字节不变，保持长发布料启用。
- 补充纳入代理的最终资源预览和全部 mip 透明度检查；实机效果待用户复测。

'''
    if '## v0.1.1' not in text:log.write_text(text.replace('# 更新日志\n\n','# 更新日志\n\n'+entry,1),encoding='utf8')
    for label in ['rest_front','rest_back','rest_side','head']:shutil.copy2(root/'reports'/('hair_proxy_after_'+label+'.png'),root/'reports'/('final_'+label+'.png'))
root_readme=SERIES/'README.md';text=root_readme.read_text(encoding='utf8')
needle='## 检查与当前限制\n\n'
note='长发布料代理使用独立全透明裁切材质，与可见头发分开。当前 v0.1.1 的[材质修复检查](reports/hair_proxy_visibility_fix.json)核对全部 LOD、原贴图、骨架、布料和映射字节不变，修复前后预览见各角色报告中的 `hair_proxy_before_*`／`hair_proxy_after_*`。v0.1.0 已收到整体良好的反馈；v0.1.1 的头发实机效果待复测。\n\n'
if note not in text:root_readme.write_text(text.replace(needle,needle+note),encoding='utf8')
(SERIES/'reports/user_feedback_v0.1.0.json').write_text(json.dumps({'date':'2026-10-15','version':'v0.1.0','overall':'User reports overall good appearance.','issue':'Many characters have moving single-color hair patches; specifically Ningguang and Weisina. Visible at close range; each character has one patch color, colors differ between characters.','individual_scene_acceptance_inferred':False},indent=2))
history=SERIES/'reports/history';history.mkdir(exist_ok=True)
for name in ['game_acceptance.json','delivery_validation.json','collection_installation.json']:
    if (SERIES/'reports'/name).exists() and not (history/('v0.1.0_'+name)).exists():shutil.copy2(SERIES/'reports'/name,history/('v0.1.0_'+name))
print('PROXY_REPAIR_DOCS_READY')
