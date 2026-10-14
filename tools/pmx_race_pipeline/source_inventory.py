"""Source-level model facts and author rules for the configured batch."""
import json,importlib.util,collections
from pathlib import Path
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parents[2];S=W/'mods/GenshinRaceCollection'

def load(root):
    c=json.loads((root/'tools/model_config.json').read_text(encoding='utf8'));spec=importlib.util.spec_from_file_location('pmx_reader',c['pmx_reader']);pmx=importlib.util.module_from_spec(spec);spec.loader.exec_module(pmx);return c,pmx.load(str(root/c['source_model']))

def inspect(root):
    c,m=load(root);p=np.array([v.co for v in m.vertices]);f=np.array(m.faces);rows=[];start=0
    for mi,a in enumerate(m.materials):
        fs=f[start:start+a.vertex_count//3];start+=len(fs);ix=np.unique(fs)
        if not len(ix):continue
        refs=collections.Counter(m.bones[b].name for i in ix for b in m.vertices[i].weight.bones if b>=0)
        rows.append({'index':mi,'name':a.name,'vertices':len(ix),'triangles':len(fs),'alpha':a.diffuse[3],'texture':a.texture,'min':p[ix].min(0).tolist(),'max':p[ix].max(0).tolist(),'bone_refs':refs.most_common(12)})
    textures=[]
    for i,t in enumerate(m.textures):
        q=Path(t.path);row={'i':i,'path':str(q),'exists':q.exists()}
        if q.exists():
            im=Image.open(q);row.update(size=im.size,mode=im.mode)
        textures.append(row)
    bones=[{'name':b.name,'parent':b.parent,'position':b.location} for b in m.bones]
    rules=[]
    for q in (root/'input/original').rglob('*.txt'):
        raw=q.read_bytes();text=None
        for enc in ['utf-8-sig','gb18030','utf-16']:
            try:text=raw.decode(enc);break
            except UnicodeError:pass
        rules.append({'path':q.relative_to(root).as_posix(),'text':text or raw.decode('utf8',errors='replace')})
    report={'id':c['id'],'source_name':m.name,'source_comment':m.comment,'vertices':len(p),'triangles':len(f),'bones':len(bones),'morphs':len(m.morphs),'height_source_units':float(np.ptp(p[:,1])),'min':p.min(0).tolist(),'max':p.max(0).tolist(),'materials':rows,'textures':textures,'source_bones':bones,'author_rules':rules}
    (root/'reports/source_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report

if __name__=='__main__':
    batch=json.loads((S/'batch_inventory.json').read_text(encoding='utf8'));out=[]
    for row in batch['characters']:
        r=inspect(Path(row['root']));out.append({'id':r['id'],'name':r['source_name'],'vertices':r['vertices'],'triangles':r['triangles'],'bones':r['bones'],'height':r['height_source_units'],'materials':[(m['index'],m['name'],m['triangles'],m['alpha']) for m in r['materials']],'missing_textures':[t['path'] for t in r['textures'] if not t['exists']],'hair_bones':[b for b in r['source_bones'] if any(x in b['name'].lower() for x in ['髪','髮','发','髮','hair','辫'])]})
    (S/'batch_source_inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps([{k:v for k,v in r.items() if k!='hair_bones'} for r in out],ensure_ascii=False,indent=2))
