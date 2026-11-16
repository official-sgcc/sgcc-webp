#!/usr/bin/env bash
set -euo pipefail

: "${DEPLOY_HOST:?Set DEPLOY_HOST in Jenkinsfile}"
: "${SERVICE:?Missing SERVICE}"
: "${IMAGE_REF:?Missing IMAGE_REF}"
: "${SSH_KEY:?Missing Jenkins SSH key binding}"
: "${SSH_USER:?Missing Jenkins SSH username binding}"
: "${KNOWN_HOSTS:?Missing Jenkins known_hosts file binding}"

if [[ ! $DEPLOY_HOST =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]]; then
    echo 'Set DEPLOY_HOST in Jenkinsfile to the shared LXC private IP.' >&2
    exit 1
fi
case "$SERVICE" in
    sgcc-webp|sgcc-webpd) ;;
    *) echo 'Unknown deployment service.' >&2; exit 1 ;;
esac
if [[ ! $IMAGE_REF =~ ^${SERVICE}:[a-zA-Z0-9_.-]+$ ]]; then
    echo 'Invalid deployment image reference.' >&2
    exit 1
fi

if ! command -v zstd >/dev/null; then
    echo 'zstd is missing on the Jenkins Docker worker.' >&2
    echo 'Install it as root in the worker LXC: apt-get update && apt-get install -y zstd' >&2
    exit 1
fi
if [[ $SSH_USER != root ]]; then
    echo 'The deployment credential must use root inside the unprivileged LXC.' >&2
    exit 1
fi
if ! ssh-keygen -F "$DEPLOY_HOST" -f "$KNOWN_HOSTS" >/dev/null; then
    echo 'Enroll the LXC SSH host key in the Jenkins known_hosts credential first; see deploy/README.md.' >&2
    exit 1
fi
ssh_options=(
    -i "$SSH_KEY" -l "$SSH_USER"
    -o BatchMode=yes -o IdentitiesOnly=yes
    # OpenSSH parses this value again; preserve spaces in Jenkins credential paths.
    -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=\"$KNOWN_HOSTS\""
    -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=3
)

ready=0
for ((attempt=0; attempt<30; attempt++)); do
    if ssh "${ssh_options[@]}" "$DEPLOY_HOST" true; then ready=1; break; fi
    sleep 2
done
if (( ! ready )); then echo 'LXC SSH did not become ready.' >&2; exit 1; fi
ssh "${ssh_options[@]}" "$DEPLOY_HOST" 'bash -s' < "$(dirname "$0")/bootstrap.sh"

# Stream directly: no image archive on either disk, and no registry credentials.
# pipefail on both ends makes compression, SSH, decompression and load failures fatal.
docker image save "$IMAGE_REF" | zstd -1 -T0 --stdout | \
    ssh "${ssh_options[@]}" "$DEPLOY_HOST" \
        "bash -o pipefail -c 'zstd --decompress --stdout | docker image load'"

printf -v remote_command 'bash -s -- %q %q' "$SERVICE" "$IMAGE_REF"
# shellcheck disable=SC2029 # Arguments are deliberately escaped on the client with printf %q.
ssh "${ssh_options[@]}" "$DEPLOY_HOST" "$remote_command" \
    < "$(dirname "$0")/run-container.sh"
