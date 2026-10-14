"""Complete race action-set names from the installed Native catalog; preserve overrides."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import xml.etree.ElementTree as ET


def index(root):
    result = {}
    for node in root.findall('action_set'):
        ident = node.get('id')
        if not ident or ident in result:
            raise ValueError(f'Missing or duplicate action-set ID: {ident}')
        result[ident] = node
    return result


def resolved_actions(ident, catalog, active=()):
    if ident in active:
        raise ValueError(f'Action-set inheritance cycle: {active + (ident,)}')
    if ident not in catalog:
        raise ValueError(f'Unresolved action set: {ident}')
    node = catalog[ident]
    base = node.get('base_set')
    actions = resolved_actions(base, catalog, active + (ident,)) if base else {}
    actions.update({n.get('type'): n.get('animation') for n in node.findall('action')})
    return actions


def requirements(native, prefix):
    if not prefix or prefix == 'human':
        raise ValueError('An independent non-human Monster naming prefix is required')
    candidates = {f'as_{prefix}{key[len("as_human"):]}': key
                  for key in native if key.startswith('as_human_')}
    if not candidates:
        raise ValueError('Native human action-set catalog is empty')
    # Native 1.4.8 has a shared male-named poses base, but callers pass AgentIsFemale.
    female = f'as_{prefix}_female_poses'
    if 'as_human_poses' in native and female not in candidates:
        candidates[female] = 'as_human_poses'
    return candidates


def complete(native_root, current_root, prefix, skeleton, legacy_prefix=None):
    native = index(native_root)
    current = index(current_root)
    if not skeleton:
        raise ValueError('A race-specific skeleton is required')
    needed = requirements(native, prefix)
    for ident, base in needed.items():
        if ident in current:
            if current[ident].get('skeleton') != skeleton:
                raise ValueError(f'Existing set uses another skeleton: {ident}')
            continue
        legacy = ('as_' + legacy_prefix + ident[len('as_' + prefix):]) if legacy_prefix else None
        if legacy in current:
            # Clone all role-specific action overrides rather than rebuilding the idle.
            node = copy.deepcopy(current[legacy])
            node.set('id', ident)
        else:
            node = ET.Element('action_set', id=ident, skeleton=skeleton,
                              movement_system='bipedal', base_set=base)
        current_root.append(node)
        current[ident] = node
    return current_root


def validate(native_root, current_root, prefix, skeleton, legacy_prefix=None):
    native, current = index(native_root), index(current_root)
    combined = native | current
    needed = requirements(native, prefix)
    missing = sorted(set(needed) - set(current))
    if missing:
        raise ValueError(f'Missing generated action-set names: {missing}')
    for ident, node in current.items():
        if node.get('skeleton') != skeleton:
            raise ValueError(f'Unexpected skeleton in {ident}')
        resolved_actions(ident, combined)
    legacy_pairs = []
    if legacy_prefix:
        for ident in needed:
            legacy = 'as_' + legacy_prefix + ident[len('as_' + prefix):]
            if legacy in current:
                if resolved_actions(ident, combined) != resolved_actions(legacy, combined):
                    raise ValueError(f'Legacy action override changed: {legacy} -> {ident}')
                legacy_pairs.append([legacy, ident])
    return {'status': 'pass', 'prefix': prefix, 'skeleton': skeleton,
            'native_catalog_count': sum(k.startswith('as_human_') for k in native),
            'required_generated_names': sorted(needed), 'canonical_count': len(needed),
            'registered_count': len(current), 'missing': [], 'legacy_pairs': legacy_pairs,
            'female_poses_base': current.get(f'as_{prefix}_female_poses').get('base_set')
                if f'as_{prefix}_female_poses' in current else None,
            'check_scope': 'XML names, skeleton declarations, inheritance and effective legacy action overrides',
            'game_verified': False}


def validate_files(native_path, action_path, prefix, skeleton, legacy_prefix=None):
    report = validate(ET.parse(native_path).getroot(), ET.parse(action_path).getroot(),
                      prefix, skeleton, legacy_prefix)
    report.update(native_sha256=hashlib.sha256(Path(native_path).read_bytes()).hexdigest(),
                  action_sets_sha256=hashlib.sha256(Path(action_path).read_bytes()).hexdigest())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--actions', type=Path, required=True)
    parser.add_argument('--prefix', required=True, help='Monster.BaseMonster or Monster.StringId')
    parser.add_argument('--skeleton', required=True)
    parser.add_argument('--legacy-prefix')
    parser.add_argument('--write', action='store_true', help='Opt in to append missing registrations')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.actions.resolve() == args.native.resolve():
        raise ValueError('The output must be a mod action-set file, never Native itself')
    native = ET.parse(args.native).getroot()
    current = ET.parse(args.actions).getroot()
    if args.write:
        complete(native, current, args.prefix, args.skeleton, args.legacy_prefix)
        validate(native, current, args.prefix, args.skeleton, args.legacy_prefix)
        ET.indent(current, space='  ')
        ET.ElementTree(current).write(args.actions, encoding='utf-8', xml_declaration=True)
    report = validate_files(args.native, args.actions, args.prefix, args.skeleton, args.legacy_prefix)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
