[![Build and Push Multiarch Docker Images](https://github.com/pedrolsazevedo/oci/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/pedrolsazevedo/oci/actions/workflows/ci.yaml)

# OCI Basic Images

Multiarch Docker images with essential development tools for testing and development in isolated environments.

## Architecture Support

All images support both **AMD64** and **ARM64** architectures, including Apple Silicon Macs.

## Available Images

All images include: `curl`, `git`, `vim`, `wget`, `unzip`, `openssl`, DNS tools, `helm`, `kubectl`, `k9s`, `mise`, `terraform`, `terragrunt`

| Image | Base | Docker Hub | Size | Family |
|-------|------|------------|------|--------|
| **Alpine** | `alpine:latest` | `psazevedo/alpine` | ~180MB | alpine |
| **Node** | `node:alpine` | `psazevedo/node` | ~280MB | alpine |
| **OpenSSL** | `alpine:latest` | `psazevedo/openssl` | ~180MB | alpine |
| **Ubuntu** | `ubuntu:24.04` | `psazevedo/ubuntu` | ~350MB | homebrew |
| **UBI** | `redhat/ubi9:latest` | `psazevedo/ubi` | ~400MB | homebrew |
| **SUSE** | `opensuse/tumbleweed:latest` | `psazevedo/suse` | ~380MB | homebrew |
| **Oracle Linux** | `oraclelinux:10` | `psazevedo/oraclelinux` | ~420MB | homebrew |

## Build System

Uses [Docker Bake](https://docs.docker.com/build/bake/) for parallel builds with shared layer caching.

Images are grouped by family to maximize cache reuse:
- **alpine-family**: alpine, node, openssl (apk-based, shared packages)
- **homebrew-family**: ubuntu, ubi, suse, oraclelinux (shared linuxbrew + mise layers)

### Quick Start

```bash
# Build all images in parallel
make build-all

# Build by family
make build-alpine    # alpine, node, openssl
make build-brew      # ubuntu, ubi, suse, oraclelinux

# Build single image
make build IMAGE=alpine

# Build OpenSSL with specific versions
make build IMAGE=openssl ALPINE_VERSION=3.17.3 OPENSSL_VERSION=3.0.8-r3

# Test build (AMD64 only, faster)
make test IMAGE=ubuntu
make test-all

# Push to registry
make push IMAGE=ubuntu VERSION=1.0.0
make push-all

# Run container
make run IMAGE=alpine

# Lint Dockerfiles
make lint
```

### Using Pre-built Images
```bash
# Alpine shell
docker run -it --rm psazevedo/alpine

# Ubuntu with volume mount
docker run -it --rm -v $(pwd):/workspace psazevedo/ubuntu

# Node.js development
docker run -it --rm -v $(pwd):/app -p 3000:3000 psazevedo/node
```

### OpenSSL Specific Usage

The OpenSSL image supports version pinning for reproducible builds:

```bash
# Build with pinned versions
make build IMAGE=openssl \
  ALPINE_VERSION=3.17.3 \
  OPENSSL_VERSION=3.0.8-r3

# Run OpenSSL operations
docker run --rm -v $(pwd):/app psazevedo/openssl:latest \
  sh -c "openssl genrsa -out /app/key.pem 2048"

# Check OpenSSL version
docker run --rm psazevedo/openssl:latest openssl version
```

## CI/CD

GitHub Actions uses `docker/bake-action` to build all images in a single job with shared GHA cache:
- **PR**: Builds all images (amd64 only) to validate
- **Release**: Builds and pushes all images (multiarch) with version from commitizen

## Automated Updates

- **Renovate Bot**: Automatically updates base images and GitHub Actions
- **GitHub Actions**: Builds and pushes multiarch images on every commit
- **Version Tagging**: Uses Commitizen for semantic versioning
