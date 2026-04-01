#!/usr/bin/env bats

# Tests for docker-bake.hcl configuration
# Run: bats tests/test_bake.bats

setup() {
    cd "$BATS_TEST_DIRNAME/.."
}

@test "docker-bake.hcl exists" {
    [ -f "docker-bake.hcl" ]
}

@test "bake file is valid and parseable" {
    docker buildx bake --print default > /dev/null 2>&1
}

@test "all group contains all 7 images" {
    local output
    output=$(docker buildx bake --print all 2>/dev/null)
    echo "$output" | jq -e '.target.alpine' > /dev/null
    echo "$output" | jq -e '.target.ubuntu' > /dev/null
    echo "$output" | jq -e '.target.ubi' > /dev/null
    echo "$output" | jq -e '.target.suse' > /dev/null
    echo "$output" | jq -e '.target.node' > /dev/null
    echo "$output" | jq -e '.target.oraclelinux' > /dev/null
    echo "$output" | jq -e '.target.openssl' > /dev/null
}

@test "alpine-family group contains alpine, node, openssl" {
    local output
    output=$(docker buildx bake --print alpine-family 2>/dev/null)
    echo "$output" | jq -e '.target.alpine' > /dev/null
    echo "$output" | jq -e '.target.node' > /dev/null
    echo "$output" | jq -e '.target.openssl' > /dev/null
    # should NOT contain homebrew images
    ! echo "$output" | jq -e '.target.ubuntu' > /dev/null 2>&1
}

@test "homebrew-family group contains ubuntu, ubi, suse, oraclelinux" {
    local output
    output=$(docker buildx bake --print homebrew-family 2>/dev/null)
    echo "$output" | jq -e '.target.ubuntu' > /dev/null
    echo "$output" | jq -e '.target.ubi' > /dev/null
    echo "$output" | jq -e '.target.suse' > /dev/null
    echo "$output" | jq -e '.target.oraclelinux' > /dev/null
    # should NOT contain alpine images
    ! echo "$output" | jq -e '.target.alpine' > /dev/null 2>&1
}

@test "all targets use correct Dockerfile paths" {
    local output
    output=$(docker buildx bake --print all 2>/dev/null)
    local images=(alpine ubuntu ubi suse)
    for img in "${images[@]}"; do
        local dockerfile
        dockerfile=$(echo "$output" | jq -r ".target.${img}.dockerfile")
        [ "$dockerfile" = "build/Dockerfile.${img}" ]
    done
    # node and openssl reuse alpine Dockerfile
    for img in node openssl; do
        local df
        df=$(echo "$output" | jq -r ".target.${img}.dockerfile")
        [ "$df" = "build/Dockerfile.alpine" ]
    done
    # oraclelinux reuses ubi Dockerfile
    local oracle_df
    oracle_df=$(echo "$output" | jq -r ".target.oraclelinux.dockerfile")
    [ "$oracle_df" = "build/Dockerfile.ubi" ]
}

@test "all targets have multiarch platforms" {
    local output
    output=$(docker buildx bake --print all 2>/dev/null)
    local images=(alpine ubuntu ubi suse node oraclelinux openssl)
    for img in "${images[@]}"; do
        echo "$output" | jq -e ".target.${img}.platforms | index(\"linux/amd64\")" > /dev/null
        echo "$output" | jq -e ".target.${img}.platforms | index(\"linux/arm64\")" > /dev/null
    done
}

@test "all targets have proper tags with DOCKER_USER and VERSION" {
    local output
    output=$(DOCKER_USER=testuser VERSION=1.0.0 docker buildx bake --print all 2>/dev/null)
    local images=(alpine ubuntu ubi suse node oraclelinux openssl)
    for img in "${images[@]}"; do
        local tags
        tags=$(echo "$output" | jq -r ".target.${img}.tags[]")
        echo "$tags" | grep -q "testuser/${img}:1.0.0"
        echo "$tags" | grep -q "testuser/${img}:latest"
    done
}

@test "openssl target has ALPINE_VERSION and OPENSSL_VERSION args" {
    local output
    output=$(docker buildx bake --print openssl 2>/dev/null)
    echo "$output" | jq -e '.target.openssl.args.ALPINE_VERSION' > /dev/null
    echo "$output" | jq -e '.target.openssl.args.OPENSSL_VERSION' > /dev/null
}

@test "all targets use cache-from and cache-to" {
    local output
    output=$(docker buildx bake --print all 2>/dev/null)
    local images=(alpine ubuntu ubi suse node oraclelinux openssl)
    for img in "${images[@]}"; do
        echo "$output" | jq -e ".target.${img}.\"cache-from\"" > /dev/null
        echo "$output" | jq -e ".target.${img}.\"cache-to\"" > /dev/null
    done
}

@test "Makefile has bake targets" {
    grep -q "docker buildx bake" Makefile
}

@test "homebrew family uses shared setup script" {
    local images=(ubuntu ubi suse)
    for img in "${images[@]}"; do
        grep -q "setup-homebrew.sh" "build/Dockerfile.${img}"
    done
    # oraclelinux reuses ubi Dockerfile which has the script
}

@test "shared setup script exists and is executable" {
    [ -x "build/scripts/setup-homebrew.sh" ]
}

@test "no duplicate homebrew setup in Dockerfiles" {
    local images=(ubuntu ubi suse oraclelinux)
    for img in "${images[@]}"; do
        ! grep -q "brew install" "build/Dockerfile.${img}"
    done
}

@test "UBI has curl openssl packages" {
    grep -q "curl" build/Dockerfile.ubi
    grep -q "openssl" build/Dockerfile.ubi
}

@test "all base images have sha256 digest pins" {
    # Dockerfiles
    grep -q "@sha256:" build/Dockerfile.alpine
    grep -q "@sha256:" build/Dockerfile.ubuntu
    grep -q "@sha256:" build/Dockerfile.ubi
    grep -q "@sha256:" build/Dockerfile.suse
    # Bake overrides
    local output
    output=$(docker buildx bake --print all 2>/dev/null)
    echo "$output" | jq -r '.target.node.args.BASE_IMAGE' | grep -q "@sha256:"
    echo "$output" | jq -r '.target.oraclelinux.args.BASE_IMAGE' | grep -q "@sha256:"
}

@test "node target passes BASE_IMAGE arg" {
    local output
    output=$(docker buildx bake --print node 2>/dev/null)
    local base
    base=$(echo "$output" | jq -r '.target.node.args.BASE_IMAGE')
    [[ "$base" == node:alpine* ]]
}

@test "oraclelinux target passes BASE_IMAGE arg" {
    local output
    output=$(docker buildx bake --print oraclelinux 2>/dev/null)
    local base
    base=$(echo "$output" | jq -r '.target.oraclelinux.args.BASE_IMAGE')
    [[ "$base" == oraclelinux:10* ]]
}
