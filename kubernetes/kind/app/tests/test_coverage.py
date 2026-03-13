"""Tests targeting low-coverage modules: status, cli, shell, cluster."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

APP_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(APP_DIR))

from cli.cli import action_cleanup, action_deploy, action_status
from core import cluster, status
from lib.shell import run, run_output


# ---------------------------------------------------------------------------
# lib/shell.py
# ---------------------------------------------------------------------------

def test_run_dry_run():
    result = run(["echo", "hi"], dry_run=True)
    assert result.returncode == 0


def test_run_success():
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0, stderr="")
        result = run(["true"], capture=True)
        assert result.returncode == 0


def test_run_failure_exits():
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=1, stderr="err")
        with pytest.raises(SystemExit):
            run(["false"], capture=True)


def test_run_no_check_no_exit():
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=1, stderr="err")
        result = run(["false"], check=False, capture=True)
        assert result.returncode == 1


def test_run_output_success():
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0, stdout="  output  ")
        assert run_output(["cmd"]) == "output"


def test_run_output_failure_returns_default():
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=1, stdout="")
        assert run_output(["cmd"], default="fallback") == "fallback"


# ---------------------------------------------------------------------------
# core/cluster.py
# ---------------------------------------------------------------------------

def test_create_cluster_already_exists(tmp_path):
    cfg = tmp_path / "cluster.yaml"
    cfg.write_text("name: test\n")
    with patch("core.cluster.cluster_exists", return_value=True):
        with patch("core.cluster.run") as mock_run:
            cluster.create_cluster("test", cfg, dry_run=True)
            calls = [c[0][0] for c in mock_run.call_args_list]
            assert not any("create" in str(c) for c in calls)


def test_create_cluster_new(tmp_path):
    cfg = tmp_path / "cluster.yaml"
    cfg.write_text("name: test\n")
    with patch("core.cluster.cluster_exists", return_value=False):
        with patch("core.cluster.run") as mock_run:
            cluster.create_cluster("test", cfg, dry_run=True)
            calls = [c[0][0] for c in mock_run.call_args_list]
            assert any("create" in str(c) for c in calls)


def test_delete_cluster_exists():
    with patch("core.cluster.cluster_exists", return_value=True):
        with patch("core.cluster.run") as mock_run:
            cluster.delete_cluster("test", dry_run=True)
            cmd = mock_run.call_args[0][0]
            assert "delete" in cmd


def test_delete_cluster_not_exists():
    with patch("core.cluster.cluster_exists", return_value=False):
        with patch("core.cluster.run_output", return_value=""):
            with patch("core.cluster.run") as mock_run:
                cluster.delete_cluster("test", dry_run=False)
                mock_run.assert_not_called()


def test_setup_hosts_already_present(tmp_path):
    hosts = tmp_path / "hosts"
    hosts.write_text("127.0.0.1 ingress.local\n")
    components = {"hosts": ["ingress.local"]}
    with patch("core.cluster.Path", return_value=hosts):
        with patch("subprocess.run") as mock_run:
            cluster.setup_hosts(components, dry_run=False)
            mock_run.assert_not_called()


def test_setup_hosts_dry_run():
    components = {"hosts": ["ingress.local"]}
    with patch("core.cluster.Path") as mock_path:
        mock_path.return_value.read_text.return_value = ""
        with patch("subprocess.run") as mock_run:
            cluster.setup_hosts(components, dry_run=True)
            mock_run.assert_not_called()


def test_setup_hosts_empty():
    with patch("core.cluster.run") as mock_run:
        cluster.setup_hosts({}, dry_run=False)
        mock_run.assert_not_called()


def test_setup_longhorn_no_nodes():
    with patch("core.cluster.run_output", return_value=""):
        with patch("core.cluster.run") as mock_run:
            cluster.setup_longhorn_prerequisites("test", dry_run=False)
            mock_run.assert_not_called()


def test_setup_longhorn_with_nodes():
    with patch("core.cluster.run_output", return_value="node1\nnode2"):
        with patch("core.cluster.run") as mock_run:
            cluster.setup_longhorn_prerequisites("test", dry_run=True)
            assert mock_run.call_count == 2


# ---------------------------------------------------------------------------
# core/status.py
# ---------------------------------------------------------------------------

def test_show_no_components():
    with patch("core.status.run") as mock_run:
        status.show({}, "test")
        mock_run.assert_not_called()


def test_show_installed_synced():
    components = {"components": {"ingress": {
        "enabled": True, "version": "4.0.0",
        "release_name": "ingress-nginx", "namespace": "ingress-nginx",
    }}}
    helm_output = '[{"name":"ingress-nginx","chart":"ingress-nginx-4.0.0"}]'
    with patch("core.status.run_output", side_effect=[helm_output, ""]):
        with patch("core.status.run"):
            status.show(components, "test")


def test_show_installed_outdated():
    components = {"components": {"ingress": {
        "enabled": True, "version": "4.1.0",
        "release_name": "ingress-nginx", "namespace": "ingress-nginx",
    }}}
    helm_output = '[{"name":"ingress-nginx","chart":"ingress-nginx-4.0.0"}]'
    with patch("core.status.run_output", side_effect=[helm_output, ""]):
        with patch("core.status.run"):
            status.show(components, "test")


def test_show_missing():
    components = {"components": {"ingress": {
        "enabled": True, "version": "4.0.0",
        "release_name": "ingress-nginx", "namespace": "ingress-nginx",
    }}}
    with patch("core.status.run_output", side_effect=["[]", ""]):
        with patch("core.status.run"):
            status.show(components, "test")


def test_show_disabled_installed():
    components = {"components": {"prometheus": {
        "enabled": False, "version": "1.0.0",
        "release_name": "prometheus", "namespace": "monitoring",
    }}}
    helm_output = '[{"name":"prometheus","chart":"kube-prometheus-stack-1.0.0"}]'
    with patch("core.status.run_output", side_effect=[helm_output, ""]):
        with patch("core.status.run"):
            status.show(components, "test")


def test_show_disabled_not_installed():
    components = {"components": {"prometheus": {
        "enabled": False, "version": "1.0.0",
        "release_name": "prometheus", "namespace": "monitoring",
    }}}
    with patch("core.status.run_output", side_effect=["[]", ""]):
        with patch("core.status.run"):
            status.show(components, "test")


def test_show_with_flux_namespace():
    components = {"components": {"ingress": {
        "enabled": True, "version": "4.0.0",
        "release_name": "ingress-nginx", "namespace": "ingress-nginx",
    }}}
    helm_output = '[{"name":"ingress-nginx","chart":"ingress-nginx-4.0.0"}]'
    with patch("core.status.run_output", side_effect=[helm_output, "flux-system"]):
        with patch("core.status.run") as mock_run:
            with patch("core.status.flux_cmd", return_value=["flux"]):
                status.show(components, "test")
                mock_run.assert_called_once()


# ---------------------------------------------------------------------------
# cli/cli.py
# ---------------------------------------------------------------------------

def _make_args(**kwargs):
    args = MagicMock()
    args.dry_run = kwargs.get("dry_run", False)
    args.profile = kwargs.get("profile", "default")
    args.cleanup = kwargs.get("cleanup", False)
    args.status = kwargs.get("status", False)
    return args


def test_action_cleanup():
    with patch("core.cluster.cluster_exists", return_value=True):
        with patch("core.cluster.run") as mock_run:
            action_cleanup(_make_args(), "test")
            assert mock_run.called


def test_action_status_no_cluster(tmp_path):
    cfg = tmp_path / "cluster.yaml"
    cfg.write_text("name: test\n")
    with patch("core.cluster.cluster_exists", return_value=False):
        action_status(_make_args(), cfg, {}, "test")


def test_action_status_with_cluster(tmp_path):
    cfg = tmp_path / "cluster.yaml"
    cfg.write_text("name: test\n")
    with patch("core.cluster.cluster_exists", return_value=True):
        with patch("core.status.show"):
            action_status(_make_args(), cfg, {}, "test")


def test_action_status_missing_config(tmp_path):
    with pytest.raises(SystemExit):
        action_status(_make_args(), tmp_path / "missing.yaml", {}, "test")


def test_action_deploy_missing_config(tmp_path):
    with pytest.raises(SystemExit):
        action_deploy(_make_args(), tmp_path / "missing.yaml", {}, "test")


def test_action_deploy_dry_run(tmp_path):
    cfg = tmp_path / "cluster.yaml"
    cfg.write_text("name: test\n")
    args = _make_args(dry_run=True)
    with patch("core.cluster.cluster_exists", return_value=False):
        with patch("core.cluster.run"):
            with patch("core.flux.bootstrap"):
                with patch("core.flux.apply_values_configmaps"):
                    with patch("core.flux.apply_manifests"):
                        with patch("core.flux.suspend_disabled"):
                            with patch("core.manifests.apply_dir"):
                                with patch("core.status.show"):
                                    action_deploy(args, cfg, {}, "test")
