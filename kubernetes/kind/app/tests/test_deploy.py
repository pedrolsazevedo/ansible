"""Unit tests for the kind deployment app (no cluster required)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

APP_DIR = Path(__file__).parent.parent.resolve()
KIND_DIR = APP_DIR.parent.resolve()
sys.path.insert(0, str(APP_DIR))

from cli.cli import REQUIRED_COMMANDS, load_components
from core import cluster, flux, manifests
from lib.shell import run, run_output


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

def test_entrypoint_exists():
    assert (KIND_DIR / "deploy.sh").exists()

def test_app_entrypoint_exists():
    assert (APP_DIR / "deploy.sh").exists()

def test_main_py_exists():
    assert (APP_DIR / "main.py").exists()


# ---------------------------------------------------------------------------
# resolve_flux
# ---------------------------------------------------------------------------

def test_resolve_flux_uses_cli_when_valid():
    with patch("shutil.which", return_value="/usr/bin/flux"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="flux version 2.8.1")
            flux.reset_flux_cmd()
            result = flux.resolve_flux()
            assert result == ["flux"]


def test_resolve_flux_falls_back_to_docker_when_missing():
    with patch("shutil.which", side_effect=lambda c: None if c == "flux" else f"/usr/bin/{c}"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            flux.reset_flux_cmd()
            result = flux.resolve_flux()
            assert result[0] == "docker"
            assert any("flux-cli" in part for part in result)


def test_resolve_flux_falls_back_to_docker_when_wrong_binary():
    with patch("shutil.which", return_value="/usr/bin/flux"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="flux - terminal multiplexer")
            flux.reset_flux_cmd()
            result = flux.resolve_flux()
            assert result[0] == "docker"


def test_resolve_flux_docker_uses_root_user():
    with patch("shutil.which", side_effect=lambda c: None if c == "flux" else f"/usr/bin/{c}"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            flux.reset_flux_cmd()
            result = flux.resolve_flux()
            assert "--user=root" in result


def test_resolve_flux_docker_passes_kubeconfig_flag():
    with patch("shutil.which", side_effect=lambda c: None if c == "flux" else f"/usr/bin/{c}"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            flux.reset_flux_cmd()
            result = flux.resolve_flux()
            assert "--kubeconfig=/root/.kube/config" in result


# ---------------------------------------------------------------------------
# load_components
# ---------------------------------------------------------------------------

def test_load_components_missing_file(tmp_path):
    assert load_components(tmp_path / "nonexistent.yaml") == {}

def test_load_components_valid(tmp_path):
    f = tmp_path / "components.yaml"
    f.write_text("components:\n  ingress:\n    enabled: true\n")
    assert load_components(f)["components"]["ingress"]["enabled"] is True

def test_load_components_empty_file(tmp_path):
    f = tmp_path / "components.yaml"
    f.write_text("")
    assert load_components(f) == {}


# ---------------------------------------------------------------------------
# get_cluster_name
# ---------------------------------------------------------------------------

def test_get_cluster_name_from_config(tmp_path):
    cfg = tmp_path / "cluster.yaml"
    cfg.write_text("name: my-cluster\n")
    assert cluster.get_cluster_name(cfg) == "my-cluster"

def test_get_cluster_name_default(tmp_path):
    assert cluster.get_cluster_name(tmp_path / "missing.yaml") == "k8s-local"


# ---------------------------------------------------------------------------
# cluster_exists
# ---------------------------------------------------------------------------

def test_cluster_exists_true():
    with patch("core.cluster.run_output", return_value="my-cluster\nother"):
        assert cluster.cluster_exists("my-cluster") is True

def test_cluster_exists_false():
    with patch("core.cluster.run_output", return_value="other-cluster"):
        assert cluster.cluster_exists("my-cluster") is False


# ---------------------------------------------------------------------------
# generate_flux_yaml
# ---------------------------------------------------------------------------

def test_generate_flux_yaml_produces_helm_repository():
    components = {"components": {"ingress": {
        "enabled": True, "repo": {"name": "ingress-nginx", "url": "https://kubernetes.github.io/ingress-nginx"},
        "chart": "ingress-nginx", "version": "4.14.2",
        "release_name": "ingress-nginx", "namespace": "ingress-nginx",
    }}}
    result = flux.generate_yaml(components)
    assert "HelmRepository" in result
    assert "HelmRelease" in result
    assert "ingress-nginx" in result


def test_generate_flux_yaml_deduplicates_repos():
    components = {"components": {
        "a": {"enabled": True, "repo": {"name": "istio", "url": "https://istio.io"}, "chart": "base", "version": "1.0.0", "release_name": "a", "namespace": "ns"},
        "b": {"enabled": True, "repo": {"name": "istio", "url": "https://istio.io"}, "chart": "istiod", "version": "1.0.0", "release_name": "b", "namespace": "ns"},
    }}
    result = flux.generate_yaml(components)
    import yaml
    docs = [d for d in yaml.safe_load_all(result) if d]
    helm_repos = [d for d in docs if d.get("kind") == "HelmRepository"]
    assert len(helm_repos) == 1


def test_generate_flux_yaml_suspend_disabled():
    components = {"components": {"prometheus": {
        "enabled": False, "repo": {"name": "prom", "url": "https://prom.io"},
        "chart": "kube-prometheus-stack", "version": "1.0.0",
        "release_name": "prometheus", "namespace": "monitoring",
    }}}
    result = flux.generate_yaml(components)
    assert "suspend: true" in result


def test_generate_flux_yaml_depends_on():
    components = {"components": {
        "a": {"enabled": True, "repo": {"name": "r", "url": "https://r.io"}, "chart": "a", "version": "1.0.0", "release_name": "a", "namespace": "ns-a"},
        "b": {"enabled": True, "repo": {"name": "r", "url": "https://r.io"}, "chart": "b", "version": "1.0.0", "release_name": "b", "namespace": "ns-b", "depends_on": ["a"]},
    }}
    result = flux.generate_yaml(components)
    assert "dependsOn" in result


# ---------------------------------------------------------------------------
# apply_manifests (manifests module)
# ---------------------------------------------------------------------------

def test_apply_dir_skips_missing_dir(tmp_path):
    with patch("core.manifests.run") as mock_run:
        manifests.apply_dir(tmp_path / "nonexistent", "test", dry_run=False)
        mock_run.assert_not_called()

def test_apply_dir_applies_yaml(tmp_path):
    (tmp_path / "manifest.yaml").write_text("apiVersion: v1\n")
    with patch("core.manifests.run") as mock_run:
        manifests.apply_dir(tmp_path, "test", dry_run=False)
        mock_run.assert_called_once()

def test_apply_extra_skips_missing(tmp_path):
    components = {"extra_manifests": ["nonexistent.yaml"]}
    with patch("core.manifests.run") as mock_run:
        manifests.apply_extra(components, tmp_path, dry_run=False)
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# bootstrap_flux
# ---------------------------------------------------------------------------

def test_bootstrap_flux_default_version():
    with patch("core.flux.run") as mock_run:
        with patch("core.flux.flux_cmd", return_value=["flux"]):
            flux.bootstrap({}, dry_run=True)
            assert mock_run.call_args_list[0][0][0] == ["flux", "install"]

def test_bootstrap_flux_pinned_version():
    with patch("core.flux.run") as mock_run:
        with patch("core.flux.flux_cmd", return_value=["flux"]):
            flux.bootstrap({"flux": {"version": "v2.3.0"}}, dry_run=True)
            assert "--version=v2.3.0" in mock_run.call_args_list[0][0][0]


# ---------------------------------------------------------------------------
# suspend_disabled
# ---------------------------------------------------------------------------

def test_suspend_disabled_calls_flux():
    components = {"components": {
        "prometheus": {"enabled": False, "release_name": "prometheus", "namespace": "monitoring"}
    }}
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch("core.flux.run") as mock_flux_run:
            with patch("core.flux.flux_cmd", return_value=["flux"]):
                flux.suspend_disabled(components, dry_run=False)
                cmd = mock_flux_run.call_args[0][0]
                assert cmd == ["flux", "suspend", "helmrelease", "prometheus", "-n", "monitoring"]

def test_suspend_skips_enabled():
    components = {"components": {
        "ingress": {"enabled": True, "release_name": "ingress-nginx", "namespace": "ingress-nginx"}
    }}
    with patch("core.flux.run") as mock_run:
        flux.suspend_disabled(components, dry_run=False)
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# Profile structure
# ---------------------------------------------------------------------------

def test_all_profiles_have_cluster_yaml():
    for profile in (KIND_DIR / "config" / "profiles").iterdir():
        if profile.is_dir():
            assert (profile / "cluster.yaml").exists(), f"{profile.name} missing cluster.yaml"

def test_no_static_flux_yaml_files():
    for profile in (KIND_DIR / "config" / "profiles").iterdir():
        if profile.is_dir():
            assert not (profile / "flux.yaml").exists(), f"{profile.name} has stale flux.yaml"
