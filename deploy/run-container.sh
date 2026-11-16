#!/usr/bin/env bash
# Runs inside the shared LXC, under the Jenkins deployment account.
set -euo pipefail

service=${1:?Missing service}
image=${2:?Missing image}
stack=sgcc-web
label=org.sgcc.deployment

case "$service" in
    sgcc-webp) host_port=8080; container_port=8080 ;;
    sgcc-webpd) host_port=8081; container_port=80 ;;
    *) echo 'Unknown deployment service.' >&2; exit 1 ;;
esac
[[ $image =~ ^${service}:[a-zA-Z0-9_.-]+$ ]] || exit 1

# Also serialize direct invocations and jobs from another Jenkins controller.
exec 9> /tmp/sgcc-web-deploy.lock
flock -w 180 9

docker image inspect "$image" >/dev/null
if [[ -z $(docker image inspect --format '{{if .Config.Healthcheck}}{{.Config.Healthcheck.Test}}{{end}}' "$image") ]]; then
    echo 'Deployment image must provide a HEALTHCHECK.' >&2
    exit 1
fi

ensure_owned() {
    local kind=$1 name=$2
    if docker "$kind" inspect "$name" >/dev/null 2>&1; then
        if [[ $(docker "$kind" inspect --format "{{index .Labels \"$label\"}}" "$name") != "$stack" ]]; then
            echo "Refusing to reuse unmanaged $kind: $name" >&2
            exit 1
        fi
    else
        docker "$kind" create --label "$label=$stack" "$name" >/dev/null
    fi
}

ensure_owned network "$stack"
run_options=(
    --detach --name "$service" --network "$stack"
    --label "$label=$stack" --restart unless-stopped
    --log-opt max-size=10m --log-opt max-file=3
    --publish "$host_port:$container_port"
)
if [[ $service == sgcc-webp ]]; then
    ensure_owned volume sgcc-webp-data
    run_options+=(--mount 'type=volume,source=sgcc-webp-data,target=/data')
fi

previous="$service-previous"
old_exists=0
old_renamed=0
new_attempted=0
committed=0
previous_image=''
if docker container inspect "$previous" >/dev/null 2>&1; then
    echo "Found $previous from an interrupted deployment; recover it before retrying." >&2
    exit 1
fi
if docker container inspect "$service" >/dev/null 2>&1; then
    if [[ $(docker container inspect --format "{{index .Config.Labels \"$label\"}}" "$service") != "$stack" ]]; then
        echo "Refusing to replace unmanaged container: $service" >&2
        exit 1
    fi
    old_exists=1
    previous_image=$(docker container inspect --format '{{.Config.Image}}' "$service")
fi

# shellcheck disable=SC2329 # Invoked indirectly by the EXIT trap.
recover() {
    local result=$?
    trap - EXIT
    if (( ! committed )); then
        echo "Deployment failed; restoring the previous $service container." >&2
        if (( new_attempted )); then docker container rm --force "$service" >/dev/null 2>&1 || true; fi
        if (( old_renamed )); then docker container rename "$previous" "$service"; fi
        if (( old_exists )); then docker container start "$service" >/dev/null; fi
    fi
    exit "$result"
}
trap recover EXIT
trap 'exit 130' INT
trap 'exit 143' HUP TERM

if (( old_exists )); then
    docker container stop --time 20 "$service" >/dev/null
    docker container rename "$service" "$previous"
    old_renamed=1
fi
new_attempted=1
docker container run "${run_options[@]}" "$image" >/dev/null

for ((attempt=0; attempt<60; attempt++)); do
    state=$(docker container inspect --format '{{.State.Running}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$service")
    if [[ $state == 'true healthy' ]]; then
        committed=1
        if (( old_renamed )); then
            docker container rm "$previous" >/dev/null
            if [[ $previous_image != "$image" ]]; then
                docker image rm "$previous_image" >/dev/null 2>&1 || true
            fi
        fi
        echo "$service is healthy on LXC port $host_port."
        exit 0
    fi
    if [[ $state != true\ * || $state == 'true unhealthy' ]]; then break; fi
    sleep 2
done

echo "$service did not become healthy within 120 seconds." >&2
docker container logs --tail 50 "$service" >&2 || true
exit 1
