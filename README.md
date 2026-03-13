# Development Tools Repository

Collection of automation tools and configurations for development workstation setup.

## Tools

### [Ansible](./ansible/)
Automated setup for Ubuntu development workstations with Docker, development tools, package managers, and cloud tools.

See [ansible/README.md](./ansible/README.md) for details.

### [OCI Images](./oci/)
Multiarch Docker images with essential development tools for testing and development in isolated environments.

See [oci/README.md](./oci/README.md) for details.

## Quick Start

```bash
# Ansible workstation setup
cd ansible
./setup.py install

# Build OCI images
cd oci
./oci.sh build all
```
