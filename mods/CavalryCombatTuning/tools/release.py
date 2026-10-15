"""Build, test, package and optionally install only CavalryCombatTuning."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MOD_ID = "CavalryCombatTuning"
MODULE = ROOT / "module" / MOD_ID


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command):
    environment = dict(os.environ)
    environment["DOTNET_CLI_UI_LANGUAGE"] = "en-US"
    result = subprocess.run([str(x) for x in command], check=True, capture_output=True,
                            text=True, encoding="utf-8", errors="strict", env=environment)
    print(result.stdout, end="")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=Path("D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord"))
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    game = args.game_root.resolve()
    descriptor = ET.parse(MODULE / "SubModule.xml").getroot()
    assert descriptor.find("Id").get("value") == MOD_ID
    version = descriptor.find("Version").get("value")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    game_inputs = [
        game / "bin/Win64_Shipping_Client/TaleWorlds.MountAndBlade.dll",
        game / "bin/Win64_Shipping_Client/TaleWorlds.Core.dll",
        game / "Modules/Sandbox/bin/Win64_Shipping_Client/SandBox.dll",
        game / "Modules/Native/SubModule.xml",
    ]
    before = {str(path): sha256(path) for path in game_inputs}
    project = ROOT / "source/Tests/CavalryCombatTuning.Tests.csproj"
    run(["dotnet", "build", project, "-c", "Release", "--nologo", f"-p:GameRoot={game}"])
    output = run([
        ROOT / "source/Tests/bin/Release/net472/CavalryCombatTuning.Tests.exe",
        game, MODULE / "ModuleData/settings.xml",
    ])
    assert "PASS 142 checks" in output
    build = ROOT / "source/Runtime/bin/Release/net472"
    binary_dir = MODULE / "bin/Win64_Shipping_Client"
    binary_dir.mkdir(parents=True, exist_ok=True)
    for name in [f"{MOD_ID}.dll", "0Harmony.dll"]:
        shutil.copy2(build / name, binary_dir / name)
    license_path = ROOT / "source/Runtime/Harmony-LICENSE.txt"
    shutil.copy2(license_path, MODULE / "Harmony-LICENSE.txt")
    shutil.copy2(ROOT / "README.md", MODULE / "README.zh-CN.md")
    shutil.copy2(ROOT / "CHANGELOG.md", MODULE / "CHANGELOG.md")
    module_files = sorted(p for p in MODULE.rglob("*") if p.is_file())
    # Runtime-generated logs are not part of a release.
    module_files = [p for p in module_files if p.name != "runtime.log"]
    hashes = {p.relative_to(MODULE).as_posix(): sha256(p) for p in module_files}
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "offline_tests.txt").write_text(output, encoding="utf-8")
    report = {
        "id": MOD_ID, "version": version, "status": "pass", "generated_utc": stamp,
        "game_version": ET.parse(game / "Modules/Native/SubModule.xml").getroot().find("Version").get("value"),
        "checks": 142, "patch_targets": [line for line in output.splitlines() if line.startswith("PATCH OK")],
        "defaults": {"ChargeDamageMultiplier": 2.5, "MountedMovementPenaltyMultiplier": 0.7, "MountedAccuracyAIOnly": False},
        "game_inputs_sha256": before, "module_files_sha256": hashes,
        "game_acceptance": "pending_user_test; game_not_started",
    }
    (reports / "release_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    package = dist / f"{MOD_ID}_{version}_{stamp}.zip"
    with zipfile.ZipFile(package, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in module_files:
            archive.write(path, str(Path(MOD_ID) / path.relative_to(MODULE)))
    # Verify archive content rather than assuming packaging succeeded.
    with zipfile.ZipFile(package) as archive:
        assert len(archive.namelist()) == len(hashes)
        for relative, expected in hashes.items():
            assert hashlib.sha256(archive.read(f"{MOD_ID}/{relative}")).hexdigest() == expected
    if args.install:
        modules_root = (game / "Modules").resolve()
        target = (modules_root / MOD_ID).resolve()
        if target.parent != modules_root or target.name != MOD_ID:
            raise ValueError("Install target outside this module")
        # Existing installations are preserved before update; user-edited settings survive reinstall.
        installed_settings = target / "ModuleData/settings.xml"
        preserved_settings = installed_settings.read_bytes() if installed_settings.exists() else None
        if target.exists():
            backup = ROOT / "build/install_backups" / stamp / MOD_ID
            shutil.copytree(target, backup)
        for source in module_files:
            destination = target / source.relative_to(MODULE)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination == installed_settings and preserved_settings is not None:
                continue
            shutil.copy2(source, destination)
        actual = {relative: sha256(target / relative) for relative in hashes}
        for relative in hashes:
            if relative == "ModuleData/settings.xml" and preserved_settings is not None:
                assert (target / relative).read_bytes() == preserved_settings
            else:
                assert actual[relative] == hashes[relative], relative
        install_report = {
            "status": "pass", "installed_path": str(target), "generated_utc": stamp,
            "existing_settings_preserved": preserved_settings is not None,
            "installed_files_sha256": actual,
        }
        (reports / "installation_validation.json").write_text(json.dumps(install_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"INSTALLED {target}")
    assert before == {str(path): sha256(path) for path in game_inputs}, "Native game inputs changed"
    source_package = dist / f"{MOD_ID}_{version}_source_{stamp}.zip"
    source_paths = [ROOT / "README.md", ROOT / "CHANGELOG.md", ROOT / "mod.json", ROOT / ".gitignore"]
    for folder in ["source", "tools", "reports", "module"]:
        for path in (ROOT / folder).rglob("*"):
            relative_parts = path.relative_to(ROOT).parts
            if path.is_file() and "obj" not in relative_parts and "__pycache__" not in relative_parts:
                if folder == "source" and "bin" in relative_parts:
                    continue
                if path.name != "runtime.log":
                    source_paths.append(path)
    with zipfile.ZipFile(source_package, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_paths):
            archive.write(path, str(Path(MOD_ID) / path.relative_to(ROOT)))
    print(f"PACKAGE {package}")
    print(f"SOURCE {source_package}")


if __name__ == "__main__":
    main()
