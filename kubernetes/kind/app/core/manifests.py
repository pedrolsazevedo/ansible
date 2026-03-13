import logging
from pathlib import Path

from lib.shell import run

log = logging.getLogger(__name__)


def apply_dir(manifest_dir: Path, label: str, dry_run: bool):
    if not manifest_dir.is_dir():
        return
    files = [
        f
        for f in manifest_dir.iterdir()
        if f.is_file() and f.suffix in (".yaml", ".yml", ".json")
    ]
    if not files:
        return
    log.info("Applying %s manifests...", label)
    for f in files:
        run(["kubectl", "apply", "-f", str(f)], dry_run=dry_run)


def apply_extra(components: dict, script_dir: Path, dry_run: bool):
    paths = components.get("extra_manifests", [])
    if not paths:
        return
    log.info("Applying extra manifests...")
    for rel_path in paths:
        manifest = script_dir / rel_path
        if not manifest.exists():
            log.warning("extra_manifest not found: %s", manifest)
            continue
        run(["kubectl", "apply", "-f", str(manifest)], dry_run=dry_run)
