import logging
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from lib.shell import run, run_output

FLUX_DOCKER_IMAGE = "ghcr.io/fluxcd/flux-cli:v2.8.1"
WAIT_TIMEOUT = "300s"
log = logging.getLogger(__name__)

_flux_cmd: list[str] | None = None


def resolve_flux() -> list[str]:
    if shutil.which("flux"):
        result = subprocess.run(["flux", "--version"], capture_output=True, text=True)
        if result.returncode == 0 and "flux version" in result.stdout:
            log.debug("Using flux CLI: %s", result.stdout.strip())
            return ["flux"]
        log.warning("'flux' binary found but is not FluxCD CLI, falling back to Docker")
    else:
        log.warning("'flux' not found in PATH, falling back to Docker")

    if not shutil.which("docker"):
        log.error("Neither flux CLI nor docker is available")
        sys.exit(1)

    log.info("Using flux via Docker image %s", FLUX_DOCKER_IMAGE)
    tmp = Path("/tmp/flux-kubeconfig.yaml")
    raw = subprocess.run(
        ["kubectl", "config", "view", "--raw", "--minify"],
        capture_output=True,
        text=True,
    ).stdout
    tmp.write_text(raw)
    tmp.chmod(0o644)

    return [
        "docker",
        "run",
        "--rm",
        "--network=host",
        "--user=root",
        "-v",
        f"{tmp}:/root/.kube/config:ro",
        FLUX_DOCKER_IMAGE,
        "--kubeconfig=/root/.kube/config",
    ]


def flux_cmd() -> list[str]:
    global _flux_cmd
    if _flux_cmd is None:
        _flux_cmd = resolve_flux()
    return _flux_cmd


def reset_flux_cmd():
    global _flux_cmd
    _flux_cmd = None


def bootstrap(components: dict, dry_run: bool):
    log.info("Bootstrapping Flux...")
    flux_version = components.get("flux", {}).get("version", "latest")
    cmd = flux_cmd() + ["install"]
    if flux_version != "latest":
        cmd.append(f"--version={flux_version}")
    run(cmd, dry_run=dry_run)
    run(
        [
            "kubectl",
            "wait",
            "--for=condition=Ready",
            "pods",
            "--all",
            "-n",
            "flux-system",
            f"--timeout={WAIT_TIMEOUT}",
        ],
        check=False,
        dry_run=dry_run,
    )


def apply_values_configmaps(components: dict, script_dir: Path, dry_run: bool):
    for name, cfg in components.get("components", {}).items():
        values_file = cfg.get("values_file")
        if not values_file:
            continue
        values_path = script_dir / values_file
        if not values_path.exists():
            log.warning("values_file for %s not found: %s", name, values_path)
            continue
        release_name = cfg["release_name"]
        namespace = cfg["namespace"]
        if not dry_run:
            run(
                ["kubectl", "create", "namespace", namespace], check=False, capture=True
            )
            manifest = run_output(
                [
                    "kubectl",
                    "create",
                    "configmap",
                    f"flux-values-{release_name}",
                    f"--from-file=values.yaml={values_path}",
                    "-n",
                    namespace,
                    "--dry-run=client",
                    "-o",
                    "yaml",
                ]
            )
            subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=manifest,
                text=True,
                check=True,
                capture_output=True,
            )


def generate_yaml(components: dict) -> str:
    docs = []
    seen_repos: set[str] = set()

    for cfg in components.get("components", {}).values():
        repo = cfg.get("repo", {})
        repo_name, repo_url = repo.get("name"), repo.get("url")
        if not repo_name or not repo_url or repo_name in seen_repos:
            continue
        seen_repos.add(repo_name)
        docs.append(
            {
                "apiVersion": "source.toolkit.fluxcd.io/v1",
                "kind": "HelmRepository",
                "metadata": {"name": repo_name, "namespace": "flux-system"},
                "spec": {"interval": "1h", "url": repo_url},
            }
        )

    for cfg in components.get("components", {}).values():
        repo_name = cfg.get("repo", {}).get("name")
        release_name, namespace = cfg.get("release_name"), cfg.get("namespace")
        chart, version = cfg.get("chart"), cfg.get("version")
        if not all([repo_name, release_name, namespace, chart, version]):
            continue

        spec: dict = {
            "interval": "10m",
            "chart": {
                "spec": {
                    "chart": chart,
                    "version": version,
                    "sourceRef": {
                        "kind": "HelmRepository",
                        "name": repo_name,
                        "namespace": "flux-system",
                    },
                }
            },
        }
        if not cfg.get("enabled", True):
            spec["suspend"] = True
        if cfg.get("timeout"):
            spec["timeout"] = cfg["timeout"]
        if cfg.get("depends_on"):
            comp_map = components["components"]
            spec["dependsOn"] = [
                {
                    "name": comp_map[d]["release_name"],
                    "namespace": comp_map[d]["namespace"],
                }
                for d in cfg["depends_on"]
                if d in comp_map
            ]
        if cfg.get("values_file"):
            spec["valuesFrom"] = [
                {
                    "kind": "ConfigMap",
                    "name": f"flux-values-{release_name}",
                    "valuesKey": "values.yaml",
                }
            ]

        docs.append(
            {
                "apiVersion": "helm.toolkit.fluxcd.io/v2",
                "kind": "HelmRelease",
                "metadata": {"name": release_name, "namespace": namespace},
                "spec": spec,
            }
        )

    return "---\n" + "---\n".join(yaml.dump(d, default_flow_style=False) for d in docs)


def apply_manifests(components: dict, dry_run: bool):
    if not components.get("components"):
        return
    log.info("Applying Flux manifests...")
    manifest = generate_yaml(components)
    if dry_run:
        log.info("[dry-run] would apply generated flux manifests")
        return
    subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=manifest,
        text=True,
        check=True,
        capture_output=True,
    )


def suspend_disabled(components: dict, dry_run: bool):
    for name, cfg in components.get("components", {}).items():
        if cfg.get("enabled", True):
            continue
        release_name, namespace = cfg.get("release_name"), cfg.get("namespace")
        if not release_name or not namespace:
            continue
        result = subprocess.run(
            ["kubectl", "get", "helmrelease", release_name, "-n", namespace],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            log.info("Suspending disabled component %s...", name)
            run(
                flux_cmd() + ["suspend", "helmrelease", release_name, "-n", namespace],
                dry_run=dry_run,
            )


def wait_for_releases(components: dict):
    for name, cfg in components.get("components", {}).items():
        if not cfg.get("enabled", True):
            continue
        release_name, namespace = cfg["release_name"], cfg["namespace"]
        log.info("Waiting for HelmRelease %s in %s...", release_name, namespace)
        result = run(
            [
                "kubectl",
                "wait",
                "helmrelease",
                release_name,
                "-n",
                namespace,
                "--for=condition=Ready",
                f"--timeout={WAIT_TIMEOUT}",
            ],
            check=False,
        )
        if result.returncode != 0:
            log.warning(
                "HelmRelease %s did not become ready within timeout", release_name
            )
