# KIND Cluster Deployment

Automated deployment for KIND (Kubernetes IN Docker) clusters using FluxCD for GitOps-style component management.

## Requirements

- Python 3.10+ — `pip install -r requirements.txt`
- Docker, kind, kubectl, helm, flux

## Quick Start

```bash
pip install -r requirements.txt

./deploy.py                        # default profile (ingress)
./deploy.py --profile monitoring   # ingress + prometheus
./deploy.py --profile minimal      # bare cluster
./deploy.py --status               # show cluster + Flux status
./deploy.py --cleanup              # delete cluster
```

`deploy.sh` is a thin shim that delegates to `main.py`.

## Structure

```
kubernetes/kind/
├── main.py                        # Main deployment script
├── deploy.sh                      # Shim → main.py
├── requirements.txt
├── config/
│   ├── profiles/
│   │   ├── default/               # Ingress only
│   │   │   ├── cluster.yaml
│   │   │   ├── components.yaml    # Component definitions (source of truth)
│   │   ├── minimal/               # Bare cluster, no components
│   │   ├── monitoring/            # Ingress + Prometheus + Grafana
│   │   ├── istio/                 # Istio service mesh
│   └── values/                    # Shared Helm values files
│       ├── ingress-nginx.yaml
│       ├── prometheus.yaml
│       └── ...
├── manifests/
│   ├── bootstrap/                 # Applied after cluster creation
│   ├── extras/                    # Applied after Flux reconciliation
│   └── examples/                  # Reference manifests (not auto-applied)
└── tests/
    ├── conftest.py
    ├── test_deploy.py             # Unit tests (no cluster required)
    ├── test_components.py         # Config validation (no cluster required)
    └── test_integration.py        # Live cluster tests
```

## Profiles

| Profile | Nodes | Components |
|---------|-------|------------|
| default | 3 (1 control-plane + 2 workers) | Ingress |
| minimal | 1 control-plane | None |
| monitoring | 3 | Ingress + Prometheus + Grafana |
| istio | 3 | Istio base + istiod + gateway |

## CLI Reference

```bash
./deploy.py [--profile NAME] [--config FILE] [--components FILE]
            [--cleanup [PROFILE]] [--status] [--dry-run] [--verbose]

# Environment variable
CLUSTER_NAME=my-cluster ./deploy.py
```

## GitOps Flow

`deploy.py` bootstraps Flux locally (no Git source needed) and applies the profile's static `flux.yaml`:

```
create_cluster → bootstrap_flux → apply_flux_values_configmaps
→ kubectl apply flux.yaml → suspend_disabled_components
→ apply bootstrap/extras manifests → wait_for_flux_releases
```

`--status` shows both Helm release state and `flux get helmreleases --all-namespaces`.

## components.yaml Schema

```yaml
flux:
  version: "v2.3.0"   # optional, defaults to latest

hosts:
  - ingress.local      # added to /etc/hosts → 127.0.0.1

components:
  my-component:
    enabled: true
    repo:
      name: my-repo
      url: https://charts.example.com
    chart: my-repo/my-chart
    version: "1.0.0"
    release_name: my-release
    namespace: my-namespace
    values_file: config/values/my-component.yaml
    depends_on:         # optional — maps to Flux HelmRelease dependsOn
      - other-component
```

When `depends_on` is set, the corresponding `HelmRelease` in `flux.yaml` will have a `dependsOn` block. Keep `components.yaml` and `flux.yaml` in sync when changing versions.

## Adding a New Profile

```bash
cp -r config/profiles/default config/profiles/my-profile
# edit cluster.yaml and components.yaml
# update flux.yaml to match components.yaml versions
./deploy.py --profile my-profile
```

## Manifests

- `manifests/bootstrap/` — applied immediately after cluster creation (namespaces, secrets, storage classes)
- `manifests/extras/` — applied after Flux reconciliation (apps, ingress rules, custom resources)
- `manifests/examples/` — reference only, not applied automatically

## Access

| Service | URL |
|---------|-----|
| Ingress | `http://ingress.local/` |
| Grafana | `http://localhost/grafana` |
| Prometheus | `http://localhost/prometheus` |

```bash
# Grafana password
kubectl get secret -n monitoring prometheus-grafana \
  -o jsonpath='{.data.admin-password}' | base64 -d
```

## Testing

```bash
# Unit + config validation (no cluster required)
pytest tests/test_deploy.py tests/test_components.py

# Integration tests (deploys a real cluster)
pytest tests/test_integration.py
```

## Code Coverage

```bash
pip install pytest-cov

# Terminal report with missing lines
pytest tests/test_deploy.py tests/test_components.py --cov=. --cov-report=term-missing

# HTML report (open htmlcov/index.html)
pytest tests/test_deploy.py tests/test_components.py --cov=. --cov-report=html

# Generate summary for git commit message
pytest tests/test_deploy.py tests/test_components.py --cov=. --cov-report=json -q
./coverage-summary.py
```

## Troubleshooting

```bash
kind get clusters
kubectl get nodes
./deploy.py --status

# Recreate cluster
./deploy.py --cleanup && ./deploy.py

# Recreate specific profile
./deploy.py --cleanup monitoring && ./deploy.py --profile monitoring

# Flux reconciliation
flux get helmreleases --all-namespaces
flux logs --all-namespaces
```
