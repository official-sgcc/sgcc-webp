# Jenkins deployment

The backend and frontend each have a root `Jenkinsfile`. Either job can create
the same unprivileged Ubuntu 26.04 LTS LXC through the Proxmox REST API; a
fixed VMID and ownership marker identify it on later runs. There is no Terraform state or
image registry. Both jobs acquire the Jenkins lock `sgcc-web-lxc` before
provisioning or deploying, and the guest also locks container replacements.

| Setting | Value |
| --- | --- |
| VMID | `120` |
| Proxmox API | `https://console.sgcc-wiki.org` |
| OS template | `local:vztmpl/ubuntu-26.04-standard_26.04-1_amd64.tar.zst` |
| Private address | `10.30.0.6/24` |
| VNet / gateway / MTU | `sgcapps` / `10.30.0.1` / `1450` |
| DNS | `163.239.1.1` |
| CPU / RAM / swap | 1 core (CPU limit 1) / 500 MiB / 0 |
| Root disk | 16 GiB on `hdd-cached` |
| Backend | `http://10.30.0.6:8080`, health at `/health/` |
| Frontend | `http://10.30.0.6:8081`, health at `/healthz` |

The node, storage, network, DNS and MTU defaults match
`sgcc_server_iac/config/sgcc_server.yml` at implementation time. Verify them
against the running cluster. The application containers and Docker share the
LXC's total 500 MiB budget; compilation and zstd compression run on Jenkins.
This budget is configured through the API, not measured on a live LXC here.

## Jenkins setup

Use a Linux amd64 agent labeled `docker` with Docker build access, Bash,
Python 3, OpenSSH client tools, `sha256sum`, and `zstd`. Docker builds use host
networking to match the existing SGCC worker's network/MTU configuration.
Required plugins are Pipeline (including Declarative), Git, Credentials Binding
and Lockable Resources. Install Lockable Resources if the existing Jenkins
installation does not have it.

Install the compression tool once as root inside the Jenkins Docker worker
LXC (CT 113), so image compression can run before the guest transfer:

```sh
apt-get update
apt-get install -y zstd
```

Create two **Pipeline from SCM** jobs, each using branch `main` and script path
`Jenkinsfile`:

- Backend: `https://github.com/official-sgcc/sgcc-webp`
- Frontend: `https://github.com/official-sgcc/sgcc-webpd`

The pipeline polls Git every five minutes. Deployments run only for `main` /
`origin/main`; pull requests and other branches build without production
credentials. For private GitHub repositories, configure SCM read credentials in
each job separately.

Both Jenkinsfiles use VMID `120` and the HTTPS API URL above. Confirm that
VMID `120` is free and reserve `10.30.0.6`; keep shared-LXC settings identical
if you change either pipeline. Use a Proxmox
API URL reachable from the **worker**; `https://localhost:8006` only works with
a worker-local forwarding tunnel. TLS verification is enabled. For a private
Proxmox CA, install its trusted CA on the worker or configure the worker's
`SSL_CERT_FILE` environment variable with the trusted CA PEM path.

The worker needs network access to the API and guest TCP 22, and the guest
needs package-repository egress. Arrange these through the existing network /
firewall configuration. The pipelines do not change host networking, firewall
policy, or reverse proxy settings.

## Credentials and SSH keys

Create a dedicated, noninteractive Ed25519 keypair for this application in a
secure administrator working directory:

```sh
ssh-keygen -t ed25519 -f sgcc-web-deploy -C jenkins-sgcc-web -N ''
```

Add these **Global** credentials to Jenkins, available only to the trusted
application jobs:

| ID | Type | Contents |
| --- | --- | --- |
| `sgcc-web-deploy` | SSH Username with private key | Username `root`; the dedicated private key; empty passphrase |
| `sgcc-web-proxmox-api` | Secret text | `USER@REALM!TOKEN_ID=TOKEN_SECRET` |
| `sgcc-web-known-hosts` | Secret file | Verified OpenSSH `known_hosts` entry for `10.30.0.6` |

The SSH key grants guest access only; do not reuse the Proxmox host or Jenkins
worker key. Jenkins derives its public key and sends that public key in the
LXC creation request. The private key never goes to Proxmox or Git. API tokens
are passed through Jenkins credential bindings, not command-line arguments.

Grant the API user and token the necessary rights on the selected VMID:
`VM.Allocate`, `VM.Audit`, `VM.PowerMgmt`, `VM.Config.CPU`, `VM.Config.Memory`,
`VM.Config.Network`, `VM.Config.Disk`, and `VM.Config.Options`. Grant
`Datastore.Audit` / `Datastore.AllocateSpace` on the relevant template and root
disk storage, and `SDN.Use` for the `sgcapps` VNet. Apply grants to both the
underlying user and privilege-separated token. The Ubuntu 26.04 LTS template
must already exist in Proxmox storage. No root password or host SSH access is used.

### First host-key enrollment

The first job run can create and start the LXC, then stop before guest access
because `sgcc-web-known-hosts` is not enrolled yet. In that LXC's Proxmox
console, read its host fingerprint:

```sh
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

From the Jenkins worker, collect its public host key:

```sh
ssh-keyscan -t ed25519 10.30.0.6 > sgcc-web-known-hosts
ssh-keygen -lf sgcc-web-known-hosts
```

Compare the fingerprints through the trusted console before uploading the
file as the Jenkins secret-file credential. Retry the job: it reuses the same
LXC. Both jobs enforce `StrictHostKeyChecking=yes`. A recreated guest needs
host-key enrollment again; a changed host key is never silently accepted.

To rotate the deployment key, add the new public key to the guest's
`/root/.ssh/authorized_keys`, update `sgcc-web-deploy`, verify a deployment,
then remove the old public key. Existing guests keep their authorized keys;
the API creation parameter only applies when creating the LXC.

## Deployment behavior

The API helper creates a new guest stopped, verifies the completed task and
configuration, then starts it. Existing guests must match the ownership marker,
node, network and resource budget. Mismatches fail without adopting, resizing,
recreating or deleting another guest. The pipeline never destroys an LXC.
Changing the template applies to newly created guests; it does not upgrade an
existing Debian or older Ubuntu guest. The bootstrap requires Ubuntu 26.04 LTS.

Creation enables **nesting only** and keeps **keyctl disabled**. Proxmox blocks
keyctl with `ENOSYS`; current runc tolerates that result during startup. The
pipeline checks actual application-container startup rather than requiring a
manual feature change. See [runc's implementation](https://github.com/opencontainers/runc/blob/main/libcontainer/standard_init_linux.go)
and [Proxmox's seccomp implementation](https://github.com/proxmox/pve-container/blob/master/src/PVE/LXC.pm).

Over verified guest SSH, `bootstrap.sh` installs Docker from Docker's official
Ubuntu APT repository and installs zstd if missing, following the
[official Docker Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/).
It then streams the image:

```text
Jenkins: docker image save | zstd -1 -T0 --stdout
                         ↓ SSH to 10.30.0.6
LXC:     zstd --decompress --stdout | docker image load
```

No image archive is written to disk. Each image has a commit/build-specific
tag. Deploying one service leaves the other container running. The previous
container is retained until the replacement passes its Docker HEALTHCHECK;
startup or health failures restore the previous container. Updates have a
brief service interruption. SQLite files live in the named volume
`sgcc-webp-data` mounted at `/data`, independently of container replacement.
Container rollback does not roll back database writes or schema changes.

If a hard interruption leaves a `*-previous` container, inspect and recover it
before retrying; the script refuses to guess or delete it. Successful updates
remove the previous container and its old image tag. Named volumes are never
deleted by deployment or rollback.

## Manual reverse proxy

Configure your external proxy to send frontend traffic to `10.30.0.6:8081` and
`/api/...` to `10.30.0.6:8080/...`, **stripping `/api`**. For example,
`/api/v1/user/...` becomes `/v1/user/...` upstream. This keeps browser API calls
on the same origin. The frontend container only serves static files and SPA
fallbacks; it does not configure your external proxy.

The frontend builds with `VITE_API_BASE_URL=/api`, including its Axios client.
Changing that URL requires rebuilding the frontend image. If you choose a
separate API origin, configure the necessary backend CORS policy separately.

Local image/transport/recovery tests do not prove live Proxmox permissions,
guest networking, the 500 MiB total runtime budget, or Jenkins plugin behavior.
The first real job run remains the environment validation.
