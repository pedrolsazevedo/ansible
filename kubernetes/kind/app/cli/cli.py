import argparse
import base64
import logging
import os
import shutil
import sys
from pathlib import Path

import yaml

from core import cluster, flux, manifests, status
from lib.shell import run_output

log = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent.parent.parent.resolve()  # kind/
REQUIRED_COMMANDS = ["kind", "kubectl", "helm"]


def check_commands():
    missing = [c for c in REQUIRED_COMMANDS if not shutil.which(c)]
    if missing:
        log.error("Missing required commands: %s", " ".join(missing))
        sys.exit(1)
    flux.reset_flux_cmd()


def load_components(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open() as f:
        return yaml.safe_load(f) or {}


def action_deploy(args, config_file: Path, components: dict, cluster_name: str):
    if args.dry_run:
        log.info("DRY RUN MODE - No changes will be made")
    if not config_file.exists():
        log.error("Config file not found: %s", config_file)
        sys.exit(1)

    log.info("Profile: %s | Config: %s", args.profile, config_file)

    if cluster.cluster_exists(cluster_name):
        status.show(components, cluster_name)

    cluster.create_cluster(cluster_name, config_file, args.dry_run)

    if any(
        cfg.get("release_name") == "longhorn"
        for cfg in components.get("components", {}).values()
        if cfg.get("enabled", True)
    ):
        cluster.setup_longhorn_prerequisites(cluster_name, args.dry_run)

    cluster.setup_hosts(components, args.dry_run)
    flux.bootstrap(components, args.dry_run)
    flux.apply_values_configmaps(components, SCRIPT_DIR, args.dry_run)
    flux.apply_manifests(components, args.dry_run)
    flux.suspend_disabled(components, args.dry_run)
    manifests.apply_dir(
        SCRIPT_DIR / "config" / "manifests" / "bootstrap", "bootstrap", args.dry_run
    )
    manifests.apply_dir(
        SCRIPT_DIR / "config" / "manifests" / "extras", "extras", args.dry_run
    )

    if args.dry_run:
        return

    flux.wait_for_releases(components)
    manifests.apply_extra(components, SCRIPT_DIR, args.dry_run)
    log.info("Setup complete!")

    if components.get("components", {}).get("prometheus", {}).get("enabled"):
        grafana_pass = run_output(
            [
                "kubectl",
                "get",
                "secret",
                "-n",
                "monitoring",
                "prometheus-grafana",
                "-o",
                "jsonpath={.data.admin-password}",
            ]
        )
        if grafana_pass:
            grafana_pass = base64.b64decode(grafana_pass).decode()
        log.info(
            "Grafana: http://localhost/grafana  |  login: admin / %s",
            grafana_pass or "pending",
        )

    status.show(components, cluster_name)


def action_status(args, config_file: Path, components: dict, cluster_name: str):
    if not config_file.exists():
        log.error("Config file not found: %s", config_file)
        sys.exit(1)
    log.info("Cluster: %s", cluster_name)
    if not cluster.cluster_exists(cluster_name):
        log.info("Status: Not found")
        return
    log.info("Status: Running")
    status.show(components, cluster_name)


def action_cleanup(args, cluster_name: str):
    cluster.delete_cluster(cluster_name, args.dry_run)


def main():
    parser = argparse.ArgumentParser(
        description="Deploy KIND cluster with FluxCD components"
    )
    parser.add_argument("--profile", default="default", metavar="NAME")
    parser.add_argument("--config", metavar="FILE")
    parser.add_argument("--components", metavar="FILE")
    parser.add_argument("--cleanup", nargs="?", const=True, metavar="CLUSTER_NAME")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    check_commands()

    profile_dir = SCRIPT_DIR / "config" / "profiles" / args.profile
    config_file = Path(args.config) if args.config else profile_dir / "cluster.yaml"
    components_file = (
        Path(args.components) if args.components else profile_dir / "components.yaml"
    )
    components = load_components(components_file)

    if args.cleanup and args.cleanup is not True:
        cluster_name = os.environ.get("CLUSTER_NAME") or args.cleanup
    elif args.status and args.profile == "default":
        current_ctx = run_output(["kubectl", "config", "current-context"])
        cluster_name = os.environ.get("CLUSTER_NAME") or (
            current_ctx.removeprefix("kind-")
            if current_ctx.startswith("kind-")
            else cluster.get_cluster_name(config_file)
        )
    else:
        cluster_name = os.environ.get("CLUSTER_NAME") or cluster.get_cluster_name(
            config_file
        )

    if args.cleanup:
        action_cleanup(args, cluster_name)
    elif args.status:
        action_status(args, config_file, components, cluster_name)
    else:
        action_deploy(args, config_file, components, cluster_name)
