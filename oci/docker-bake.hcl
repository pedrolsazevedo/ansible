variable "DOCKER_USER" { default = "psazevedo" }
variable "VERSION" { default = "latest" }
variable "ALPINE_VERSION" { default = "latest" }
variable "OPENSSL_VERSION" { default = "" }

group "default" { targets = ["alpine", "ubuntu", "ubi", "suse", "node", "oraclelinux", "openssl"] }
group "all" { targets = ["alpine", "ubuntu", "ubi", "suse", "node", "oraclelinux", "openssl"] }
group "alpine-family" { targets = ["alpine", "node", "openssl"] }
group "homebrew-family" { targets = ["ubuntu", "ubi", "suse", "oraclelinux"] }

target "_common" {
  platforms = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=gha"]
  cache-to   = ["type=gha,mode=max"]
}

target "alpine" {
  inherits   = ["_common"]
  dockerfile = "build/Dockerfile.alpine"
  tags       = ["${DOCKER_USER}/alpine:${VERSION}", "${DOCKER_USER}/alpine:latest"]
}

target "ubuntu" {
  inherits   = ["_common"]
  dockerfile = "build/Dockerfile.ubuntu"
  tags       = ["${DOCKER_USER}/ubuntu:${VERSION}", "${DOCKER_USER}/ubuntu:latest"]
}

target "ubi" {
  inherits   = ["_common"]
  dockerfile = "build/Dockerfile.ubi"
  tags       = ["${DOCKER_USER}/ubi:${VERSION}", "${DOCKER_USER}/ubi:latest"]
}

target "suse" {
  inherits   = ["_common"]
  dockerfile = "build/Dockerfile.suse"
  tags       = ["${DOCKER_USER}/suse:${VERSION}", "${DOCKER_USER}/suse:latest"]
}

target "node" {
  inherits   = ["_common"]
  dockerfile = "build/Dockerfile.alpine"
  tags       = ["${DOCKER_USER}/node:${VERSION}", "${DOCKER_USER}/node:latest"]
  args = {
    BASE_IMAGE = "node:alpine@sha256:ad82ecad30371c43f4057aaa4800a8ed88f9446553a2d21323710c7b937177fc"
  }
}

target "oraclelinux" {
  inherits   = ["_common"]
  dockerfile = "build/Dockerfile.ubi"
  tags       = ["${DOCKER_USER}/oraclelinux:${VERSION}", "${DOCKER_USER}/oraclelinux:latest"]
  args = {
    BASE_IMAGE = "oraclelinux:10@sha256:49fd6c2f84b01823e4730a3ba654708d69e730f92e859da58d982be37263b34f"
  }
}

target "openssl" {
  inherits   = ["_common"]
  dockerfile = "build/Dockerfile.alpine"
  tags       = ["${DOCKER_USER}/openssl:${VERSION}", "${DOCKER_USER}/openssl:latest"]
  args = {
    ALPINE_VERSION  = ALPINE_VERSION
    OPENSSL_VERSION = OPENSSL_VERSION
  }
}
