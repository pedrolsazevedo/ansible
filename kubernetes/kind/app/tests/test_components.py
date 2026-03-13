"""Validate components.yaml and flux.yaml for all profiles (no cluster required)."""

import re
from pathlib import Path

import pytest
import yaml

KIND_DIR = Path(__file__).parent.parent.parent.resolve()
PROFILES_DIR = KIND_DIR / "config" / "profiles"
REQUIRED_COMPONENT_FIELDS = {"release_name", "namespace", "version", "chart", "repo"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def enabled_components(data: dict) -> dict:
    return {k: v for k, v in data.get("components", {}).items() if v.get("enabled", True)}


# ---------------------------------------------------------------------------
# components.yaml - parametrised over all profiles that have one
# ---------------------------------------------------------------------------

def pytest_generate_tests(metafunc):
    if "profile_name" in metafunc.fixturenames and "components_data" in metafunc.fixturenames:
        profiles = [
            p for p in PROFILES_DIR.iterdir()
            if p.is_dir() and (p / "components.yaml").exists()
        ]
        metafunc.parametrize(
            "profile_name,components_data",
            [(p.name, yaml.safe_load((p / "components.yaml").read_text()) or {}) for p in profiles],
            ids=[p.name for p in profiles],
        )


def test_components_yaml_is_valid_yaml(profile_name, components_data):
    assert isinstance(components_data, dict)


def test_enabled_components_have_required_fields(profile_name, components_data):
    for comp, cfg in enabled_components(components_data).items():
        missing = REQUIRED_COMPONENT_FIELDS - cfg.keys()
        assert not missing, f"{profile_name}/{comp} missing fields: {missing}"


def test_enabled_components_have_repo(profile_name, components_data):
    for comp, cfg in enabled_components(components_data).items():
        repo = cfg.get("repo", {})
        assert repo.get("name"), f"{profile_name}/{comp} missing repo.name"
        assert repo.get("url"), f"{profile_name}/{comp} missing repo.url"


def test_versions_are_semver(profile_name, components_data):
    for comp, cfg in enabled_components(components_data).items():
        version = cfg.get("version", "")
        assert re.match(r"^\d+\.\d+\.\d+", version), \
            f"{profile_name}/{comp} version '{version}' is not semver"


def test_chart_format(profile_name, components_data):
    for comp, cfg in enabled_components(components_data).items():
        chart = cfg.get("chart", "")
        assert re.match(r"^[a-z0-9-]+$", chart), \
            f"{profile_name}/{comp} chart '{chart}' is not a valid chart name"


def test_namespaces_are_valid(profile_name, components_data):
    for comp, cfg in enabled_components(components_data).items():
        ns = cfg.get("namespace", "")
        assert re.match(r"^[a-z0-9-]+$", ns), \
            f"{profile_name}/{comp} namespace '{ns}' is invalid"


def test_values_files_exist(profile_name, components_data):
    for comp, cfg in enabled_components(components_data).items():
        vf = cfg.get("values_file")
        if vf:
            assert (KIND_DIR / vf).exists(), \
                f"{profile_name}/{comp} values_file '{vf}' not found"


def test_depends_on_references_valid_components(profile_name, components_data):
    all_comps = set(components_data.get("components", {}).keys())
    for comp, cfg in components_data.get("components", {}).items():
        for dep in cfg.get("depends_on", []):
            assert dep in all_comps, \
                f"{profile_name}/{comp} depends_on '{dep}' which does not exist"


def test_hosts_are_valid_hostnames(profile_name, components_data):
    for host in components_data.get("hosts", []):
        assert re.match(r"^[a-z0-9.-]+$", host), \
            f"{profile_name} host '{host}' is not a valid hostname"


# ---------------------------------------------------------------------------
# Profile-specific assertions
# ---------------------------------------------------------------------------

def test_monitoring_profile_has_prometheus_enabled():
    data = yaml.safe_load(
        (PROFILES_DIR / "monitoring" / "components.yaml").read_text()
    )
    assert data["components"]["prometheus"]["enabled"] is True


def test_minimal_profile_has_no_enabled_components():
    minimal = PROFILES_DIR / "minimal" / "components.yaml"
    if not minimal.exists():
        pytest.skip("minimal profile has no components.yaml")
    data = yaml.safe_load(minimal.read_text()) or {}
    assert not enabled_components(data), "minimal profile should have no enabled components"


# ---------------------------------------------------------------------------
# flux.yaml validation
# ---------------------------------------------------------------------------

def test_no_static_flux_yaml_files():
    """flux.yaml is generated dynamically — no static files should exist."""
    for profile in PROFILES_DIR.iterdir():
        if profile.is_dir():
            assert not (profile / "flux.yaml").exists(), \
                f"{profile.name} has a static flux.yaml (should be generated)"
