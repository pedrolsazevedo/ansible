[![Docker Repository on Quay](https://quay.io/repository/psazevedo/openssl/status "Docker Repository on Quay")](https://quay.io/repository/psazevedo/openssl) | [![CI/CD](https://github.com/pedrolsazevedo/openssl/actions/workflows/bump_version.yaml/badge.svg?branch=main)](https://github.com/pedrolsazevedo/openssl/actions/workflows/bump_version.yaml)

# OpenSSL Docker Image
This is a Docker image that includes OpenSSL based on Alpine Linux.

## Usage

To use this image, run the following command:

Replace `<version>` with the specific version of the image you wish to use, such as `latest`, `1.1.1k`, etc.

```bash
docker run -it --rm psazevedo/openssl:<version>
```

### How to Use

Once the container is running, you can use any OpenSSL command as you normally would. For example, to generate a private key and CSR, you could use the following commands:

**Generate a private key**
```bash
openssl genrsa -out example.com.key 2048
```
**Generate a CSR**
```bash
openssl req -new -key example.com.key -out example.com.csr
```

You can also use the `-v` flag to mount a local directory as a volume in the container, so you can access the generated files on your local machine. For example:
Generate a private key and CSR and save them to a local directory
This will generate a private key and CSR in your current working directory, and you can access them on your local machine.

```bash
docker run --rm
-v $(pwd):/app
psazevedo/openssl:latest
sh -c "openssl genrsa -out /app/example.com.key 2048 && openssl req -new -key /app/example.com.key -out /app/example.com.csr"
```

## Building the Image

To build the Docker image, run the following command:
```bash
docker build -t psazevedo/openssl:<version> \
  --build-arg ALPINE_VERSION=<alpine-version> \
  --build-arg OPENSSL_VERSION=<openssl-version> \
  .
```

Replace `<version>` with the specific version tag you wish to use for the image, `<alpine-version>` with the version of Alpine Linux you want to use, and `<openssl-version>` with the version of OpenSSL you want to use.

For example, to build an image with OpenSSL 3.0.8 based on Alpine Linux 3.17.3, run:

```bash
docker build -t openssl-amd64 \
  --build-arg ALPINE_VERSION=3.17.3 \
  --build-arg OPENSSL_VERSION=3.0.8-r3 \
  -f Dockerfile.amd64 \
  --platform linux/amd64 .
```

Building multi arch image

```bash
docker buildx build --file Dockerfile.multi \
  -t psazevedo/openssl:3.0.8-r3-alpine3.17.3 \
  --platform linux/amd64,linux/arm64 \
  --build-arg ALPINE_VERSION=3.17.3 \
  --build-arg OPENSSL_VERSION=3.0.8-r3 \
  --push .
```

## Running the Container

To run the container, use the `docker run` command as shown in the Usage section. You can replace `<version>` with the version tag you built or pulled from Docker Hub.

For example, to run the container with the `1.1.1k-alpine3.14` tag, run:
```bash
docker run --rm -it psazevedo/openssl:1.1.1k-alpine3.14 version
```

This will output the version of OpenSSL installed in the container.

## OpenSSL Help

Standard commands
asn1parse         ca                ciphers           cmp
cms               crl               crl2pkcs7         dgst
dhparam           dsa               dsaparam          ec
ecparam           enc               engine            errstr
fipsinstall       gendsa            genpkey           genrsa
help              info              kdf               list
mac               nseq              ocsp              passwd
pkcs12            pkcs7             pkcs8             pkey
pkeyparam         pkeyutl           prime             rand
rehash            req               rsa               rsautl
s_client          s_server          s_time            sess_id
smime             speed             spkac             srp
storeutl          ts                verify            version
x509

Message Digest commands (see the `dgst' command for more details)
blake2b512        blake2s256        md4               md5
rmd160            sha1              sha224            sha256
sha3-224          sha3-256          sha3-384          sha3-512
sha384            sha512            sha512-224        sha512-256
shake128          shake256          sm3

Cipher commands (see the `enc' command for more details)
aes-128-cbc       aes-128-ecb       aes-192-cbc       aes-192-ecb
aes-256-cbc       aes-256-ecb       aria-128-cbc      aria-128-cfb
aria-128-cfb1     aria-128-cfb8     aria-128-ctr      aria-128-ecb
aria-128-ofb      aria-192-cbc      aria-192-cfb      aria-192-cfb1
aria-192-cfb8     aria-192-ctr      aria-192-ecb      aria-192-ofb
aria-256-cbc      aria-256-cfb      aria-256-cfb1     aria-256-cfb8
aria-256-ctr      aria-256-ecb      aria-256-ofb      base64
bf                bf-cbc            bf-cfb            bf-ecb
bf-ofb            camellia-128-cbc  camellia-128-ecb  camellia-192-cbc
camellia-192-ecb  camellia-256-cbc  camellia-256-ecb  cast
cast-cbc          cast5-cbc         cast5-cfb         cast5-ecb
cast5-ofb         des               des-cbc           des-cfb
des-ecb           des-ede           des-ede-cbc       des-ede-cfb
des-ede-ofb       des-ede3          des-ede3-cbc      des-ede3-cfb
des-ede3-ofb      des-ofb           des3              desx
rc2               rc2-40-cbc        rc2-64-cbc        rc2-cbc
rc2-cfb           rc2-ecb           rc2-ofb           rc4
rc4-40
