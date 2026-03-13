import logging
import subprocess
from pathlib import Path

from lib.shell import run, run_output

WAIT_TIMEOUT = "300s"
log = logging.getLogger(__name__)


def cluster_exists(name: str) -> bool:
    return name in run_output(["kind", "get", "clusters"]).splitlines()


def get_cluster_name(config_file: Path) -> str:
    if config_file.exists():
        import yaml

        with config_file.open() as f:
            data = yaml.safe_load(f) or {}
        if "name" in data:
            return data["name"]
    return "k8s-local"


def create_cluster(name: str, config_file: Path, dry_run: bool):
    if cluster_exists(name):
        log.info("Cluster '%s' exists, skipping creation", name)
    else:
        log.info("Creating cluster '%s'...", name)
        run(
            ["kind", "create", "cluster", "--name", name, "--config", str(config_file)],
            dry_run=dry_run,
        )
    if not dry_run:
        run(["kubectl", "config", "use-context", f"kind-{name}"])
    run(
        [
            "kubectl",
            "wait",
            "--for=condition=Ready",
            "nodes",
            "--all",
            f"--timeout={WAIT_TIMEOUT}",
        ],
        dry_run=dry_run,
    )


def delete_cluster(name: str, dry_run: bool):
    if not cluster_exists(name):
        log.info("Cluster '%s' does not exist", name)
        clusters = run_output(["kind", "get", "clusters"])
        log.info("Available clusters:\n%s", clusters or "  (none)")
        return
    log.info("Deleting cluster '%s'...", name)
    run(["kind", "delete", "cluster", "--name", name], dry_run=dry_run)
    log.info("Cleanup complete!")


def setup_longhorn_prerequisites(cluster_name: str, dry_run: bool):
    nodes = run_output(["kind", "get", "nodes", "--name", cluster_name]).splitlines()
    if not nodes:
        return
    log.info("Enabling iscsid on kind nodes...")
    for node in nodes:
        run(
            ["docker", "exec", node, "systemctl", "enable", "--now", "iscsid"],
            dry_run=dry_run,
            check=False,
        )


def setup_hosts(components: dict, dry_run: bool):
    hostnames = components.get("hosts", [])
    if not hostnames:
        return
    hosts_path = Path("/etc/hosts")
    current = hosts_path.read_text()
    for hostname in hostnames:
        if f"127.0.0.1 {hostname}" in current or f"127.0.0.1\t{hostname}" in current:
            continue
        log.info("Adding %s to /etc/hosts", hostname)
        if not dry_run:
            subprocess.run(
                ["sudo", "tee", "-a", str(hosts_path)],
                input=f"127.0.0.1 {hostname}\n",
                text=True,
                check=True,
                stdout=subprocess.DEVNULL,
            )
