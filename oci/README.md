[![Build and Push Multiarch Docker Images](https://github.com/pedrolsazevedo/oci/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/pedrolsazevedo/oci/actions/workflows/ci.yaml)

# OCI Basic Images

Multiarch Docker images with essential development tools for testing and development in isolated environments.

## Architecture Support

All images support both **AMD64** and **ARM64** architectures, including Apple Silicon Macs.

## Available Images

All images include: `curl`, `git`, `vim`, `wget`, `unzip`, `openssl`, DNS tools, `helm`, `kubectl`, `k9s`, `mise`, `terraform`, `terragrunt`

| Image | Base | Docker Hub | Size | Notes |
|-------|------|------------|------|-------|
| **Alpine** | `alpine:latest` | `psazevedo/alpine` | ~180MB | |
| **Ubuntu** | `ubuntu:24.04` | `psazevedo/ubuntu` | ~350MB | |
| **UBI** | `redhat/ubi9:latest` | `psazevedo/ubi` | ~400MB | |
| **SUSE** | `opensuse/tumbleweed:latest` | `psazevedo/suse` | ~380MB | |
| **Node** | `node:alpine` | `psazevedo/node` | ~280MB | |
| **Oracle Linux** | `oraclelinux:10` | `psazevedo/oraclelinux` | ~420MB | |
| **OpenSSL** | `alpine:latest` | `psazevedo/openssl` | ~180MB | Supports version pinning |

## Quick Start

### Using Pre-built Images
```bash
# Alpine shell
docker run -it --rm psazevedo/alpine

# Ubuntu with volume mount
docker run -it --rm -v $(pwd):/workspace psazevedo/ubuntu

# Node.js development
docker run -it --rm -v $(pwd):/app -p 3000:3000 psazevedo/node
```

### Using Makefile
```bash
# Build single image
make build IMAGE=alpine

# Build all images
make build-all

# Build OpenSSL with specific versions
make build IMAGE=openssl ALPINE_VERSION=3.17.3 OPENSSL_VERSION=3.0.8-r3

# Test build (AMD64 only)
make test IMAGE=ubuntu

# Run container
make run IMAGE=alpine

# Push to registry
make push IMAGE=ubuntu VERSION=1.0.0
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

## Local Development

### Build and Run Images
```bash
# Build images
make build IMAGE=alpine       # Single image
make build-all                # All images

# Test build (AMD64 only, faster)
make test IMAGE=ubuntu

# Run container
make run IMAGE=alpine

# Clean up
make clean
```

### OpenSSL Certificate Generation

All images include OpenSSL for certificate operations:

```bash
# Generate private key
openssl genrsa -out private.key 2048

# Generate certificate signing request
openssl req -new -key private.key -out cert.csr

# Generate self-signed certificate
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes

# View certificate details
openssl x509 -in cert.pem -text -noout

# Test SSL connection
openssl s_client -connect example.com:443
```

## 🔄 Automated Updates

- **Renovate Bot**: Automatically updates base images and GitHub Actions
- **GitHub Actions**: Builds and pushes multiarch images on every commit
- **Version Tagging**: Uses Commitizen for semantic versioning
