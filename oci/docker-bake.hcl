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
    BASE_IMAGE = "node:alpine@sha256:cf38e1f3c28ac9d81cdc0c51d8220320b3b618780e44ef96a39f76f7dbfef023"
  }
}

target "oraclelinux" {
  inherits   = ["_common"]
  dockerfile = "build/Dockerfile.ubi"
  tags       = ["${DOCKER_USER}/oraclelinux:${VERSION}", "${DOCKER_USER}/oraclelinux:latest"]
  args = {
    BASE_IMAGE = "oraclelinux:10@sha256:de4684812d77e65c65e96cfb926d6f2c2d2c66348f21d271f1164500a4878635"
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
