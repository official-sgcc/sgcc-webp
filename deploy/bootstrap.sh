#!/usr/bin/env bash
# Idempotent guest setup; this script never runs on the Proxmox host.
set -euo pipefail

if (( $(id -u) != 0 )); then
    echo 'Use the root account inside the unprivileged LXC for guest setup.' >&2
    exit 1
fi
. /etc/os-release
if [[ $ID != ubuntu || $VERSION_ID != 26.04 ]]; then
    echo 'This deployment expects an Ubuntu 26.04 LTS LXC.' >&2
    exit 1
fi
export DEBIAN_FRONTEND=noninteractive

if ! command -v docker >/dev/null; then
    apt-get -o Acquire::Retries=5 update
    apt-get -o Acquire::Retries=5 install -y --no-install-recommends ca-certificates curl zstd
    install -d -m 0755 /etc/apt/keyrings
    curl --fail --silent --show-error --retry 5 --retry-all-errors \
        https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod 0644 /etc/apt/keyrings/docker.asc
    cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
    apt-get -o Acquire::Retries=5 update
    apt-get -o Acquire::Retries=5 install -y --no-install-recommends docker-ce docker-ce-cli containerd.io
elif ! command -v zstd >/dev/null; then
    apt-get -o Acquire::Retries=5 update
    apt-get -o Acquire::Retries=5 install -y --no-install-recommends zstd
fi

systemctl enable --now docker
docker info >/dev/null
