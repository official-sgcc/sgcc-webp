#!/usr/bin/env python3
"""Create or verify the shared LXC using only the Proxmox HTTPS API."""

import ipaddress
import json
import os
import re
import ssl
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

MARKER = "jenkins-managed:official-sgcc/sgcc-web"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, url):
        # API authentication must never be forwarded to a login/redirect target.
        return None


class Proxmox:
    def __init__(self, endpoint, token):
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or "CHANGE_ME" in endpoint
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path.rstrip("/") not in ("", "/api2/json")
        ):
            raise ValueError(
                "Set PVE_URL to a reachable, trusted Proxmox HTTPS API URL."
            )
        if not re.fullmatch(r"[^\s!=]+![^\s=]+=[^\s]+", token):
            raise ValueError(
                "API credential must contain USER@REALM!TOKEN_ID=TOKEN_SECRET."
            )
        self.base = endpoint.rstrip("/")
        if not self.base.endswith("/api2/json"):
            self.base += "/api2/json"
        self.authorization = "PVEAPIToken=" + token
        # Uses the agent's trust store, including SSL_CERT_FILE when configured.
        self.context = ssl.create_default_context()
        self.opener = build_opener(HTTPSHandler(context=self.context), NoRedirect())

    def request(self, method, path, payload=None):
        body = urlencode(payload).encode() if payload is not None else None
        request = Request(
            self.base + path,
            data=body,
            method=method,
            headers={
                "Authorization": self.authorization,
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "sgcc-jenkins-deploy/1.0",
            },
        )
        try:
            with self.opener.open(request, timeout=30) as response:
                return json.load(response)["data"]
        except HTTPError as error:
            # Never print request headers, credentials, or an echoed response body.
            raise RuntimeError(
                f"Proxmox {method} {path} failed: HTTP {error.code}; "
                "check API permissions, settings and the Proxmox task log."
            ) from None
        except URLError as error:
            raise RuntimeError(
                f"Cannot reach the Proxmox API: {error.reason}"
            ) from None

    def wait(self, node, upid):
        path = f"/nodes/{quote(node, safe='')}/tasks/{quote(upid, safe='')}/status"
        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            status = self.request("GET", path)
            if status["status"] == "stopped":
                if status.get("exitstatus") != "OK":
                    raise RuntimeError(
                        "Proxmox task failed; inspect its log in the Proxmox UI."
                    )
                return
            time.sleep(2)
        raise RuntimeError(
            "Proxmox task timed out; inspect it before retrying. It was not cancelled."
        )


def settings():
    def required(name):
        value = os.environ.get(name, "").strip()
        if not value or "CHANGE_ME" in value:
            raise ValueError(f"Set {name} in both Jenkinsfiles.")
        return value

    node = required("PVE_NODE")
    storage = required("PVE_STORAGE")
    bridge = required("PVE_BRIDGE")
    for value in (node, storage, bridge):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
            raise ValueError("Invalid Proxmox node, storage or bridge name.")
    vmid = int(required("LXC_VMID"))
    if not 100 <= vmid <= 999999999:
        raise ValueError("LXC_VMID must be between 100 and 999999999.")
    address = ipaddress.IPv4Interface(required("LXC_IPV4_CIDR"))
    if str(address.ip) != required("DEPLOY_HOST"):
        raise ValueError("DEPLOY_HOST must match LXC_IPV4_CIDR.")
    gateway = ipaddress.IPv4Address(required("LXC_GATEWAY"))
    if gateway not in address.network or address.ip in (
        address.network.network_address,
        address.network.broadcast_address,
        gateway,
    ):
        raise ValueError(
            "The LXC address and gateway must be usable addresses in the same subnet."
        )
    dns = str(ipaddress.IPv4Address(required("LXC_DNS")))
    mtu = int(required("LXC_MTU"))
    if not 1280 <= mtu <= 65535:
        raise ValueError("Invalid LXC_MTU.")
    template = required("PVE_TEMPLATE")
    if not re.fullmatch(
        r"[\w.-]+:vztmpl/ubuntu-26\.04-standard_[\w.-]+_amd64\.tar\.(?:zst|xz|gz)",
        template,
    ):
        raise ValueError(
            "PVE_TEMPLATE must name an existing Ubuntu 26.04 LTS amd64 standard template."
        )
    public_key = Path(required("SSH_PUBLIC_KEY_FILE")).read_text().strip()
    if "\n" in public_key or not re.match(
        r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-\S+) \S+", public_key
    ):
        raise ValueError(
            "Expected one OpenSSH public key derived from the deployment credential."
        )
    desired = {
        "vmid": vmid,
        "hostname": "sgcc-web",
        "description": MARKER,
        "ostemplate": template,
        "ostype": "ubuntu",
        "arch": "amd64",
        "unprivileged": 1,
        # runc tolerates ENOSYS when keyctl is blocked; no root-only feature flag.
        "features": "nesting=1",
        "cores": 1,
        "cpulimit": 1,
        "memory": 500,
        "swap": 0,
        "rootfs": f"{storage}:16",
        "net0": f"name=eth0,bridge={bridge},ip={address},gw={gateway},mtu={mtu}",
        "nameserver": dns,
        "ssh-public-keys": public_key,
        "onboot": 1,
        "start": 0,
    }
    return node, vmid, desired


def properties(value):
    return dict(item.split("=", 1) for item in value.split(",") if "=" in item)


def ensure_lxc(api, node, vmid, desired):
    base = f"/nodes/{quote(node, safe='')}/lxc"
    matches = [
        item
        for item in api.request("GET", "/cluster/resources?type=vm")
        if int(item["vmid"]) == vmid
    ]
    if matches:
        existing = matches[0]
        if existing["type"] != "lxc" or existing["node"] != node:
            raise RuntimeError(
                "Requested VMID belongs to another guest or node; nothing was changed."
            )
    else:
        print(f"Creating shared unprivileged LXC {vmid}: 1 core, 500 MiB, no swap.")
        api.wait(node, api.request("POST", base, desired))

    config = api.request("GET", f"{base}/{vmid}/config?current=1")
    if config.get("description", "").strip() != MARKER:
        raise RuntimeError(
            "Refusing to adopt an LXC without this application's ownership marker."
        )
    if config.get("lock") or config.get("template"):
        raise RuntimeError(
            "The shared LXC is locked or is a template; inspect it before retrying."
        )
    if config.get("ostype") != desired["ostype"]:
        raise RuntimeError(
            "Existing LXC OS differs from the Ubuntu configuration; use a fresh VMID "
            "or migrate the guest manually. Nothing was replaced."
        )
    for name in ("unprivileged", "cores", "cpulimit", "memory", "swap", "onboot"):
        if float(config.get(name, -1)) != desired[name]:
            raise RuntimeError(
                f"Existing LXC setting {name} differs from the Jenkins configuration."
            )
    if config.get("hostname") != desired["hostname"] or config.get("arch") != "amd64":
        raise RuntimeError(
            "Existing LXC hostname or architecture differs from the Jenkins configuration."
        )
    if properties(config.get("features", "")).get("nesting") != "1":
        raise RuntimeError("The shared LXC must have nesting enabled.")
    actual_network = properties(config.get("net0", ""))
    for key, value in properties(desired["net0"]).items():
        if actual_network.get(key) != value:
            raise RuntimeError(
                f"Existing LXC network setting {key} differs; nothing was changed."
            )
    if config.get("rootfs", "").split(":", 1)[0] != desired["rootfs"].split(":", 1)[0]:
        raise RuntimeError(
            "Existing LXC storage differs from the Jenkins configuration."
        )

    current = api.request("GET", f"{base}/{vmid}/status/current")
    if current["status"] != "running":
        api.wait(node, api.request("POST", f"{base}/{vmid}/status/start", {}))
    print(f"Shared LXC {vmid} is ready at {properties(desired['net0'])['ip']}.")


def main():
    node, vmid, desired = settings()
    api = Proxmox(os.environ.get("PVE_URL", ""), os.environ.get("PVE_API_TOKEN", ""))
    ensure_lxc(api, node, vmid, desired)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        sys.exit(str(error))
