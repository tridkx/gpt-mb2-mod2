"""Reuse the incremental build machinery with explicit Mingyu head/neck scope."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
code=(ROOT/'tools/prepare_hair_shape.py').read_text()
code=code.replace('v1.1.5','v1.1.6').replace('v1.1.4','v1.1.5').replace('hair_shape','head_neck')
code=code.replace('4e4e921944451b8612471426177159d8f1ee1ec96a35b9a1892e541edeb3a0ef','578da1d8839be6f4ac7d9504eeb15d1a1f4a1538755c6c9c965a79fef1d18159')
code=code.replace('hair_geometry/HairGeometry.dll','head_neck_geometry/HeadNeckGeometry.dll')
code=code.replace("assert old['Name']=='sx_mingyu_head_00' or old['Name'].startswith('sx_mingyu_head_00.lod'),old['Name']","assert old['Name'].startswith('sx_mingyu_head_') or old['Name'].split('.lod')[0]=='sx_mingyu_body_02',old['Name']")
code=code.replace('assert len(changed)==4','assert len(changed)==28').replace('other_52_meshes_identical','other_28_meshes_identical')
exec(compile(code,__file__,'exec'))
