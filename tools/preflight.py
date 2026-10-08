"""Run the installed skill's read-only preflight with workspace-local helpers."""
import runpy
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    skill = Path.home() / '.codex/skills/bannerlord-equipment-mod/scripts/preflight.py'
    if not skill.is_file():
        raise SystemExit(f'Missing installed skill preflight: {skill}')
    args = sys.argv[1:]
    for option, value in (
        ('--workspace', root),
        ('--helpers', root / 'tools/asset_helpers'),
    ):
        if not any(arg == option or arg.startswith(option + '=') for arg in args):
            args.extend([option, str(value)])
    sys.argv = [str(skill), *args]
    runpy.run_path(str(skill), run_name='__main__')


if __name__ == '__main__':
    main()
