"""Wire a measured skirt candidate into its own reproducible mod pipeline."""
import sys,json,re,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
WS=Path(__file__).resolve().parents[1];ROOT=WS/'mods'/sys.argv[1];version=sys.argv[2];key=sys.argv[3]
cfgpath=ROOT/'tools/model_config.json';cfg=json.loads(cfgpath.read_text());cfg['reference_skirt_candidate']=key;cfg['skirt_reference_calibration']={'waist_modes':['pelvis','reference'],'follow_candidates':[.7,.8,.9],'calf_candidates':[.15,.25,.35,.45]};cfgpath.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
descriptor=ROOT/f'module/{ROOT.name}/SubModule.xml';t=ET.parse(descriptor);t.find('Version').set('value',version);t.write(descriptor,encoding='utf-8',xml_declaration=True)
script=ROOT/'tools/rig_model.py';s=script.read_text()
if "cfg.get('skirt_clearance_fit')" not in s:
    needle="    if rec['kind']=='long_hair':"
    insertion="    if rec['kind']=='skirt' and cfg.get('skirt_clearance_fit'):\n        fitted=np.load(ROOT/cfg['skirt_clearance_fit']);assert str(fitted['object'])==o.name\n        d=fitted['P'];w=fitted['W'];alpha=fitted['A'];a['W']=w;a['A']=alpha\n"
    assert needle in s;s=s.replace(needle,insertion+needle,1);script.write_text(s)
script=ROOT/'tools/export_geometry.py';s=script.read_text()
if 'keep_shape=' not in s:
    needle="        if lod and r['texture_key'] not in ['face','eye','lash']:"
    assert needle in s;s=s.replace(needle,"        keep_shape=cfg.get('skirt_clearance_fit') and (r['kind']=='skirt' or r['part']=='legs')\n        if lod and r['texture_key'] not in ['face','eye','lash'] and not keep_shape:")
if "q=np.rint(w*255)" not in s:
    needle="                    q=np.floor(w*255).astype(int);q[w.argmax()]+=255-q.sum()";assert needle in s
    s=s.replace(needle,needle+"\n                    if r['kind']=='skirt' and cfg.get('skirt_clearance_fit'):\n                        q=np.rint(w*255).astype(int);assert q.sum()==255")
script.write_text(s)
package=ROOT/json.loads((ROOT/'mod.json').read_text())['package'];base=ROOT/'build/repair_baseline_v1.0.0'/package.relative_to(ROOT);digest=hashlib.sha256(base.read_bytes()).hexdigest()
script=ROOT/'tools/verify_release.py';s=script.read_text();s=re.sub(r"'baseline_package_sha256':(?:None|'[^']*')",f"'baseline_package_sha256':'{digest}'",s);s=re.sub(r"'baseline_reason':'[^']*'","'baseline_reason':'smooth calf-follow repair; preserve accepted rest contour'",s);s=s.replace("'skirt_leg_penetration_repair_complete':False,'rear_contour_restored':True","'skirt_leg_penetration_game_confirmed':False,'rest_contour_preserved':True");s=s.replace('Original skirt/leg contact remains unresolved.','Skirt contact reduced offline; game cloth remains untested.');script.write_text(s)
report=ROOT/'reports/release_validation.json'
if report.exists():
    r=json.loads(report.read_text());r['baseline_reason']='smooth calf-follow repair; preserve accepted rest contour';r['skirt_leg_penetration_game_confirmed']=False;r.pop('skirt_leg_penetration_repair_complete',None);report.write_text(json.dumps(r,indent=2))
readme=ROOT/'README.md';s=readme.read_text(encoding='utf-8');s=re.sub(r'v\d+\.\d+\.\d+',version,s.split('## v1.0.2')[0]);s+=f'\n## {version} 裙摆随动返修\n\n参考用户认可的第一套裙摆随动逻辑，按本套原始裙片与解剖标记独立校准，选择 {key}。下裙摆恢复平滑同侧小腿影响，中心交界的小腿影响平滑归零，避免四骨截断切换。保留原版全部静态坐标、UV、拓扑、其他部件权重和布料 Alpha；四级 LOD 保留裙摆/腿部轮廓。未扩大后摆，未隐藏腿部。source/SkirtClearanceFit.npz 保存可重建的裙摆权重。\n\n完整跑步、拉弓、骑乘及 16 个待机采样检查最终 TPAC。离线腿部接触与变形指标见 reference_skirt_validation.json；游戏布料未验证，不能声称全部穿模已消除。游戏测试由用户完成。历史版本和交付包保留。\n';readme.write_text(s,encoding='utf-8');print('REFERENCE_REPAIR_CONFIGURED',ROOT.name,version,key)
