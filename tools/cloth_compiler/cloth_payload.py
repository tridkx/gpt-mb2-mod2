"""Experimental reader/writer for native b97e0f10 cloth preprocessing data.

Layout inferred from installed native samples and shipped GPU shader sources.
All fields are represented; the reader rejects trailing or truncated bytes.
"""
from pathlib import Path
import struct
import numpy as np

FIELDS = [
    ('rest_lengths', '<f4', 1), ('constraints', '<u2', 2),
    ('constraint_sets', '<i4', 8), ('dummy_sets', '<i4', 2),
    ('rest_positions', '<u4', 1), ('rest_normals', '<u4', 1),
    ('render_to_sim', '<u4', 1), ('dummy_indices', '<u4', 1),
    ('max_distances', '<f4', 1), ('inverse_areas', '<f4', 1),
    ('bone_indices', 'u1', 1), ('bone_weights', '<f4', 1),
    ('anchors', '<u4', 1),
]


def read(raw):
    if isinstance(raw, (str, Path)):
        raw = Path(raw).read_bytes()
    if len(raw) < 56:
        raise ValueError('truncated cloth header')
    scale, nc, nv, normal_start, sim_start, nd = struct.unpack_from('<f5I', raw)
    result = dict(anchor_scale=scale, constraint_count=nc, vertex_count=nv,
                  normal_start=normal_start, simulation_start=sim_start,
                  dummy_index_count=nd, bounds=np.frombuffer(raw, '<f4', 8, 24).copy())
    offset = 56
    result['offsets'] = {}
    for name, dtype, width in FIELDS:
        count = struct.unpack_from('<I', raw, offset)[0]
        result['offsets'][name] = dict(offset=offset, count=count)
        offset += 4
        size = np.dtype(dtype).itemsize * count * width
        if offset + size > len(raw):
            raise ValueError(f'truncated {name}: {count} elements at {offset}')
        a = np.frombuffer(raw, dtype, count * width, offset).copy()
        result[name] = a.reshape((-1, width)) if width > 1 else a
        offset += size
    if offset != len(raw):
        raise ValueError(f'unparsed tail: {len(raw)-offset} bytes')
    return result


def write(data):
    result = bytearray(struct.pack('<f5I', data['anchor_scale'], data['constraint_count'],
                       data['vertex_count'], data['normal_start'], data['simulation_start'],
                       data['dummy_index_count']))
    result.extend(np.asarray(data['bounds'], '<f4').tobytes())
    for name, dtype, width in FIELDS:
        array = np.asarray(data[name], dtype)
        assert array.size % width == 0
        result.extend(struct.pack('<I', array.size // width))
        result.extend(array.tobytes())
    return bytes(result)


def editor_read(path):
    raw = Path(path).read_bytes()
    offset = 0
    arrays = {}
    for name, stride in [('positions', 16), ('unused', 16), ('vertices', 92), ('faces', 12)]:
        count = struct.unpack_from('<I', raw, offset)[0]
        offset += 4
        arrays[name] = (count, raw[offset:offset+count*stride])
        offset += count * stride
    nv, vertices = arrays['vertices']
    v_dtype = np.dtype({'names': ['position', 'normal', 'color'],
                       'formats': ['<u4', ('<f4', 4), ('u1', 4)],
                       'offsets': [0, 4, 84], 'itemsize': 92})
    v = np.frombuffer(vertices, v_dtype, nv)
    positions = np.frombuffer(arrays['positions'][1], '<f4').reshape(-1, 4)
    faces = np.frombuffer(arrays['faces'][1], '<i4').reshape(-1, 3)
    return dict(positions=positions[:, :3], vertices=v, faces=faces,
                triangles=v['position'][faces], alpha=v['color'][:, 3],
                normals=v['normal'][:, :3])


def decode_positions(data):
    packed = data['rest_positions'].reshape(-1, 2).astype(np.uint64)
    x, y = packed[:, 0], packed[:, 1]
    q = np.column_stack((x >> 11, ((x & 0x7ff) << 10) | (y >> 22), (y & 0x3ffffe) >> 1))
    # Rest positions use runtime [-10,+10] bounds multiplied by REST_POS=10.
    return q / 0x1fffff * 200 - 100


if __name__ == '__main__':
    import sys
    for path in sys.argv[1:]:
        raw = Path(path).read_bytes()
        data = read(raw)
        assert write(data) == raw
        print(Path(path).name, 'exact roundtrip', len(raw), 'bytes',
              data['vertex_count'], 'positions', data['constraint_count'], 'constraints')
