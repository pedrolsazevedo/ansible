import logging
import subprocess
import sys

log = logging.getLogger(__name__)


def run(
    cmd: list[str], *, check=True, capture=False, dry_run=False
) -> subprocess.CompletedProcess:
    log.debug("$ %s", " ".join(cmd))
    if dry_run:
        log.info("[dry-run] %s", " ".join(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    result = subprocess.run(cmd, text=True, capture_output=capture)
    if check and result.returncode != 0:
        stderr = result.stderr.strip() if capture else ""
        log.error("Command failed: %s\n%s", " ".join(cmd), stderr)
        sys.exit(result.returncode)
    return result


def run_output(cmd: list[str], *, default="") -> str:
    result = subprocess.run(cmd, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else default
