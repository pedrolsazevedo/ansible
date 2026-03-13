import pytest
import yaml
from pathlib import Path

APP_DIR = Path(__file__).parent.parent.resolve()
KIND_DIR = APP_DIR.parent.resolve()
PROFILES_DIR = KIND_DIR / "config" / "profiles"
PROFILES = [p.name for p in PROFILES_DIR.iterdir() if p.is_dir()]
PROFILES_WITH_COMPONENTS = [p for p in PROFILES if (PROFILES_DIR / p / "components.yaml").exists()]


@pytest.fixture
def kind_dir():
    return KIND_DIR


@pytest.fixture
def app_dir():
    return APP_DIR


@pytest.fixture(params=PROFILES_WITH_COMPONENTS)
def profile_components(request):
    path = PROFILES_DIR / request.param / "components.yaml"
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    return request.param, data
