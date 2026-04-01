.PHONY: help build build-all push push-all test test-all clean run lint

DOCKER_USER ?= psazevedo
VERSION ?= latest

# OpenSSL specific versions
ALPINE_VERSION ?= latest
OPENSSL_VERSION ?=

PLATFORM ?= linux/$(shell uname -m | sed s/x86_64/amd64/ | sed s/aarch64/arm64/)
IMAGES := alpine ubuntu ubi suse node oraclelinux openssl

export DOCKER_USER VERSION ALPINE_VERSION OPENSSL_VERSION

help:
	@echo "OCI Image Management (Docker Bake)"
	@echo ""
	@echo "Usage: make <target> [IMAGE=<name>] [VERSION=<tag>]"
	@echo ""
	@echo "Targets:"
	@echo "  build         - Build single image (requires IMAGE=name)"
	@echo "  build-all     - Build all images in parallel"
	@echo "  build-alpine  - Build alpine family (alpine, node, openssl)"
	@echo "  build-brew    - Build homebrew family (ubuntu, ubi, suse, oraclelinux)"
	@echo "  push          - Build and push single image (requires IMAGE=name)"
	@echo "  push-all      - Build and push all images"
	@echo "  test          - Test build single image (requires IMAGE=name)"
	@echo "  test-all      - Test build all images"
	@echo "  run           - Run container shell (requires IMAGE=name)"
	@echo "  lint          - Lint all Dockerfiles with hadolint"
	@echo "  clean         - Remove local images"
	@echo ""
	@echo "Available images: $(IMAGES)"
	@echo ""
	@echo "OpenSSL specific options:"
	@echo "  ALPINE_VERSION  - Alpine base version (default: latest)"
	@echo "  OPENSSL_VERSION - Pin OpenSSL version (e.g., 3.0.8-r3)"
	@echo ""
	@echo "Examples:"
	@echo "  make build IMAGE=alpine"
	@echo "  make build IMAGE=openssl ALPINE_VERSION=3.17.3 OPENSSL_VERSION=3.0.8-r3"
	@echo "  make build-all"
	@echo "  make push IMAGE=ubuntu VERSION=1.0.0"
	@echo "  make run IMAGE=alpine"

build:
	@test -n "$(IMAGE)" || (echo "ERROR: IMAGE required (e.g., make build IMAGE=alpine)" && exit 1)
	docker buildx bake $(IMAGE) --set '*.platform=$(PLATFORM)' --load

build-all:
	docker buildx bake all --set '*.platform=$(PLATFORM)' --load

build-alpine:
	docker buildx bake alpine-family --set '*.platform=$(PLATFORM)' --load

build-brew:
	docker buildx bake homebrew-family --set '*.platform=$(PLATFORM)' --load

push:
	@test -n "$(IMAGE)" || (echo "ERROR: IMAGE required" && exit 1)
	docker buildx bake $(IMAGE) --push

push-all:
	docker buildx bake all --push

test:
	@test -n "$(IMAGE)" || (echo "ERROR: IMAGE required" && exit 1)
	docker buildx bake $(IMAGE) --set '*.platform=$(PLATFORM)' --load

test-all:
	docker buildx bake all --set '*.platform=$(PLATFORM)' --load

run:
	@test -n "$(IMAGE)" || (echo "ERROR: IMAGE required" && exit 1)
	docker run -it --rm $(DOCKER_USER)/$(IMAGE):latest

lint:
	@$(foreach img,$(IMAGES),echo "Linting Dockerfile.$(img)..." && hadolint build/Dockerfile.$(img);)

clean:
	@$(foreach img,$(IMAGES),docker rmi -f $(DOCKER_USER)/$(img):latest $(DOCKER_USER)/$(img):$(VERSION) 2>/dev/null || true;)
	@echo "Cleaned local images"
