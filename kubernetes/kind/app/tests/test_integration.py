"""Integration tests - require a running KIND cluster (deploy with default profile first)."""

import subprocess
import time
from pathlib import Path

import pytest

KIND_DIR = Path(__file__).parent.parent.parent.resolve()
DEPLOY = KIND_DIR / "app" / "main.py"


def kubectl(*args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["kubectl", *args], text=True, capture_output=True, check=check)


def flux(*args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["flux", *args], text=True, capture_output=True, check=check)


# ---------------------------------------------------------------------------
# Session-scoped cluster lifecycle
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def cluster():
    subprocess.run([str(DEPLOY), "--profile", "default"], check=True)
    yield
    subprocess.run([str(DEPLOY), "--cleanup"], check=False)


# ---------------------------------------------------------------------------
# Cluster health
# ---------------------------------------------------------------------------

def test_nodes_are_ready():
    result = kubectl("wait", "--for=condition=Ready", "nodes", "--all", "--timeout=120s")
    assert result.returncode == 0


def test_flux_system_namespace_exists():
    result = kubectl("get", "ns", "flux-system", "--no-headers")
    assert result.returncode == 0


def test_flux_controllers_are_ready():
    result = kubectl("wait", "--for=condition=Ready", "pods", "--all",
                     "-n", "flux-system", "--timeout=120s")
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# Ingress
# ---------------------------------------------------------------------------

def test_ingress_helmrelease_is_ready():
    result = kubectl("wait", "--for=condition=Ready",
                     "helmrelease/ingress-nginx",
                     "-n", "ingress-nginx", "--timeout=120s")
    assert result.returncode == 0


def test_ingress_controller_pod_is_ready():
    result = kubectl("wait", "--for=condition=ready", "pod",
                     "-n", "ingress-nginx",
                     "-l", "app.kubernetes.io/component=controller",
                     "--timeout=120s")
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# HTTP access via ingress
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ingress_test_deployed():
    manifest = KIND_DIR / "config" / "manifests" / "examples" / "ingress-test.yaml"
    subprocess.run(["kubectl", "apply", "-f", str(manifest)], check=True)
    subprocess.run(["kubectl", "wait", "--for=condition=available",
                    "deployment/ingress-test", "-n", "ingress-test",
                    "--timeout=120s"], check=True)
    yield
    subprocess.run(["kubectl", "delete", "-f", str(manifest)], check=False)


def test_http_access(ingress_test_deployed):
    for _ in range(10):
        result = subprocess.run(
            ["curl", "-s", "http://localhost/", "--max-time", "5"],
            text=True, capture_output=True,
        )
        if "Welcome to nginx" in result.stdout:
            return
        time.sleep(2)
    pytest.fail(f"HTTP access failed. Last response: {result.stdout[:200]}")
