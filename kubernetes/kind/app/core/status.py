import json
import logging

from lib.shell import run, run_output
from core.flux import flux_cmd

log = logging.getLogger(__name__)


def show(components: dict, cluster_name: str):
    comps = components.get("components", {})
    if not comps:
        return

    log.info("")
    log.info("Component Status (Helm):")
    log.info("%-20s %-12s %-15s %-15s", "COMPONENT", "DESIRED", "CURRENT", "STATUS")
    log.info("%-20s %-12s %-15s %-15s", "---------", "-------", "-------", "------")

    for name, cfg in comps.items():
        enabled = cfg.get("enabled", True)
        desired = cfg.get("version", "-")
        release_name = cfg.get("release_name", name)
        namespace = cfg.get("namespace", "default")

        releases = run_output(["helm", "list", "-n", namespace, "-o", "json"])
        current, installed = "-", False
        if releases:
            for r in json.loads(releases):
                if r["name"] == release_name:
                    installed = True
                    current = r["chart"].rsplit("-", 1)[-1]
                    break

        if enabled:
            status = (
                ("✓ Synced" if current == desired else "⚠ Outdated")
                if installed
                else "⚠ Missing"
            )
        else:
            status = "⚠ Disabled (installed)" if installed else "✓ Disabled"
            desired = "disabled"

        log.info("%-20s %-12s %-15s %-15s", name, desired, current, status)

    if run_output(["kubectl", "get", "ns", "flux-system", "--no-headers"]):
        log.info("")
        log.info("Component Status (Flux HelmReleases):")
        run(flux_cmd() + ["get", "helmreleases", "--all-namespaces"], check=False)
