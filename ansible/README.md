# Ansible Workstation Setup

Automated Ubuntu development workstation configuration using Ansible.

## Features

- **System Preparation**: Essential packages and system configuration
- **Development Tools**: VS Code, Chrome, and basic dev packages
- **Docker**: Docker Engine with user permissions
- **Package Managers**: Homebrew, mise, pyenv, nvm, tfenv
- **Cloud Tools**: Azure CLI, Storage Explorer, azcopy
- **Container Tools**: kubectl, Helm, kind, Podman (optional)
- **Rancher Desktop**: Container management platform
- **SSH Keys**: Automated SSH key generation

## Quick Start

```bash
# Install on local machine
./setup.py install

# Run specific roles with tags
./setup.py install --tags docker,package_managers

# Dry run (check mode)
./setup.py install --check
```

## Testing

```bash
# Syntax check
./setup.py test --syntax

# Docker-based integration test
./setup.py test --docker
```

## Configuration

Version management is centralized in `vars/versions.yml`. Update versions there instead of individual role defaults.

## CI/CD

- **GitHub Actions**: Automated testing on push/PR
- **Renovate**: Automated dependency updates
- **Pre-commit**: Code quality checks

## Structure

```
ansible/
├── playbooks/       # Ansible playbooks
├── roles/           # Ansible roles
├── inventories/     # Inventory files
├── vars/            # Centralized variables
├── tests/           # Test playbooks and configs
└── setup.py         # CLI wrapper
```
