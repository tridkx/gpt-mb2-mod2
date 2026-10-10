"""Run the installed skill's read-only preflight for this workspace."""
import runpy
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    skill = Path.home() / '.codex/skills/bannerlord-equipment-mod/scripts/preflight.py'
    if not skill.is_file():
        raise SystemExit(f'Missing installed skill preflight: {skill}')
    args = sys.argv[1:]
    if not any(arg == '--workspace' or arg.startswith('--workspace=') for arg in args):
        args.extend(['--workspace', str(root)])
    sys.argv = [str(skill), *args]
    runpy.run_path(str(skill), run_name='__main__')


if __name__ == '__main__':
    main()
