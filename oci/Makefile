.PHONY: help build build-all push push-all test clean run

DOCKER_USER ?= psazevedo
VERSION ?= latest
PLATFORMS ?= linux/amd64,linux/arm64

# OpenSSL specific versions (can be overridden)
ALPINE_VERSION ?= latest
OPENSSL_VERSION ?=

IMAGES := alpine ubuntu ubi suse node oraclelinux openssl

help:
	@echo "OCI Image Management"
	@echo ""
	@echo "Usage: make <target> [IMAGE=<name>] [VERSION=<tag>]"
	@echo ""
	@echo "Targets:"
	@echo "  build         - Build single image (requires IMAGE=name)"
	@echo "  build-all     - Build all images"
	@echo "  push          - Push single image (requires IMAGE=name)"
	@echo "  push-all      - Push all images"
	@echo "  test          - Test build single image (requires IMAGE=name)"
	@echo "  test-all      - Test build all images"
	@echo "  run           - Run container shell (requires IMAGE=name)"
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
	docker buildx build \
		--platform $(PLATFORMS) \
		--tag $(DOCKER_USER)/$(IMAGE):$(VERSION) \
		--tag $(DOCKER_USER)/$(IMAGE):latest \
		--build-arg ALPINE_VERSION=$(ALPINE_VERSION) \
		--build-arg OPENSSL_VERSION=$(OPENSSL_VERSION) \
		--file build/Dockerfile.$(IMAGE) \
		--load \
		.

build-all:
	@$(foreach img,$(IMAGES),make build IMAGE=$(img);)

push:
	@test -n "$(IMAGE)" || (echo "ERROR: IMAGE required" && exit 1)
	docker buildx build \
		--platform $(PLATFORMS) \
		--tag $(DOCKER_USER)/$(IMAGE):$(VERSION) \
		--tag $(DOCKER_USER)/$(IMAGE):latest \
		--build-arg ALPINE_VERSION=$(ALPINE_VERSION) \
		--build-arg OPENSSL_VERSION=$(OPENSSL_VERSION) \
		--file build/Dockerfile.$(IMAGE) \
		--push \
		.

push-all:
	@$(foreach img,$(IMAGES),make push IMAGE=$(img);)

test:
	@test -n "$(IMAGE)" || (echo "ERROR: IMAGE required" && exit 1)
	docker buildx build \
		--platform linux/amd64 \
		--build-arg ALPINE_VERSION=$(ALPINE_VERSION) \
		--build-arg OPENSSL_VERSION=$(OPENSSL_VERSION) \
		--file build/Dockerfile.$(IMAGE) \
		--load \
		.

test-all:
	@$(foreach img,$(IMAGES),make test IMAGE=$(img);)

run:
	@test -n "$(IMAGE)" || (echo "ERROR: IMAGE required" && exit 1)
	docker run -it --rm $(DOCKER_USER)/$(IMAGE):latest

clean:
	@$(foreach img,$(IMAGES),docker rmi -f $(DOCKER_USER)/$(img):latest $(DOCKER_USER)/$(img):$(VERSION) 2>/dev/null || true;)
	@echo "Cleaned local images"
