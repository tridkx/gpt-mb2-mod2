"""Hair-only incremental build from the verified v1.1.6 package."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
code=(ROOT/'tools/prepare_hair_shape.py').read_text()
code=code.replace('v1.1.5','v1.1.7').replace('v1.1.4','v1.1.6').replace('hair_shape','back_hair')
code=code.replace('4e4e921944451b8612471426177159d8f1ee1ec96a35b9a1892e541edeb3a0ef','e4ecf83f7dad35a438ccbe8617af21d6d568f9b9a46ef5cf3e2694aeb5593c7c')
code=code.replace('hair_geometry/HairGeometry.dll','back_hair_geometry/BackHairGeometry.dll')
code=code.replace(" and old['ClothingMaterial']==new['ClothingMaterial']", "")
exec(compile(code,__file__,'exec'))
