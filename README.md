[![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brightgreen.svg)](http://commitizen.github.io/cz-cli/)

# Ansible Development Workstation Setup

Automated setup for Ubuntu development workstations with Docker, development tools, package managers, and cloud tools.

## Quick Start

```bash
# Interactive installation
./setup.py install

# Install everything
./setup.py install --all

# Install specific components
./setup.py install --tags docker,mise

# List available roles
./setup.py list

# Run tests
./setup.py test
```

## What Gets Installed

- **System Prep**: Essential packages, apt updates
- **Basic Tools**: vim, wget, git, VS Code, Chrome
- **Docker**: Docker Engine with user permissions
- **Package Managers**: Homebrew, tfenv, pyenv, nvm
- **Mise**: Polyglot runtime manager
- **Azure Tools**: Azure CLI, Storage Explorer, AzCopy
- **Container Tools**: kubectl, Podman, Helm, kind
- **Rancher Desktop**: Container management desktop application
- **SSH Keys**: Ed25519 key generation

## Configuration

Customize settings:
- `inventories/development/group_vars/all.yml` - User and path settings
- `inventories/development/group_vars/versions.yml` - Version management and feature flags
- `roles/*/defaults/main.yml` - Role-specific defaults (rarely needed)

## Testing

### Quick Start

```bash
# Local dry-run tests (safe, no changes to system)
./setup.py test

# Docker-based integration tests
./setup.py test --docker

# Syntax check only
./setup.py test --syntax
```

### Test Types

**Local Tests (Dry-run)**
- Safe to run on your local machine
- Uses `--check` mode to validate without making changes
- Tests syntax, individual roles, and full playbook

**Docker Tests (Integration)**
- Full integration tests in isolated Ubuntu 24.04 container
- Actually installs everything
- Tests idempotence (no changes on second run)
- Uses [geerlingguy/docker-ubuntu2404-ansible](https://hub.docker.com/r/geerlingguy/docker-ubuntu2404-ansible)

**CI/CD**
- GitHub Actions automatically runs tests on push/PR
- See `.github/workflows/ci.yml`

### Manual Testing

```bash
# Test specific role
ansible-playbook playbooks/site.yml --tags docker --check

# Run in container manually
docker compose -f tests/docker-compose.yml up -d
ansible-playbook tests/test.yml -i tests/inventory.yml
docker compose -f tests/docker-compose.yml down -v
```

## Automated Updates

Renovate automatically checks for updates weekly and creates PRs for:
- Kubernetes tools (kubectl, kind)
- Node.js and Python versions
- Rancher Desktop
- Docker images in tests
- Ansible collections

Configure in `renovate.json` or trigger manually via GitHub Actions.