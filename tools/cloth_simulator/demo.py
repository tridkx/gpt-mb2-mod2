"""Self-contained procedural cloth example; no game files or network required."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloth_compiler.cook_cloth import cook
from cloth_compiler.cloth_payload import read, decode_positions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[2]/'build/cloth_simulator/demo')
    args = parser.parse_args()
    dest = args.output.resolve()
    if dest.exists() and any(dest.iterdir()):
        parser.error('choose an empty output directory')
    dest.mkdir(parents=True, exist_ok=True)
    nx, nz = 9, 13
    pos = np.array([[x, .035, z] for z in np.linspace(1.2, .45, nz) for x in np.linspace(-.25, .25, nx)])
    tri = []
    for z in range(nz-1):
        for x in range(nx-1):
            a = z*nx+x
            tri.extend([[a, a+nx, a+1], [a+1, a+nx, a+nx+1]])
    mesh = dict(name='procedural_cloth', guid='00000000-0000-0000-0000-000000000001',
                metamesh='demo', lod=0, positions=pos.tolist(), indices=np.array(tri).ravel().tolist(),
                normals=np.tile([0., -1., 0], (len(pos), 1)).tolist(),
                alpha=([0]*nx+[100]*(len(pos)-nx)), weights=[], bones=[])
    raw, _ = cook(mesh)
    (dest/'cloth.bin').write_bytes(raw)
    (dest/'cloth.mesh.json').write_text(json.dumps(mesh), encoding='utf-8')
    rest = decode_positions(read(raw))
    anchors = np.repeat(rest[None], 90, axis=0)
    phase = np.linspace(0, 2*np.pi, 90)
    anchors[:, :, 0] += (.035*np.sin(phase))[:, None]
    capsules = np.repeat(np.array([[[0., 0, .65, .09], [0., 0, .88, .09]]])[None], 90, axis=0)
    capsules[:, 0, :, 0] += (.025*np.sin(phase))[:, None]
    np.savez_compressed(dest/'motion.npz', anchors=anchors, capsules=capsules)
    return subprocess.call([sys.executable, '-X', 'utf8', str(Path(__file__).with_name('run.py')),
        'simulate', '--payload', str(dest/'cloth.bin'), '--mesh', str(dest/'cloth.mesh.json'),
        '--motion', str(dest/'motion.npz'), '--fps', '60', '--multiplier', '1',
        '--output', str(dest/'result')])


if __name__ == '__main__':
    sys.exit(main())
