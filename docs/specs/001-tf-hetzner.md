---
status: complete
---

# Create a Hetzner Server with Terraform

## Goal

Provision one cost-optimized ARM64 server on Hetzner Cloud and generate an Ansible inventory for it.

## Requirements

- Location: Helsinki (`hel1`)
- Server type: `cax31` (ARM64, 8 vCPU, 16 GB RAM)
- OS: Ubuntu 24.04 LTS
- Networking: public IPv4 and IPv6 with a Hetzner firewall
- Allow inbound UDP port 41641 for direct Tailscale connections.
- Allow inbound TCP port 8000 for temporary public FastAPI access.
- Do not expose SSH on the public network.
- Use cloud-init to install Tailscale and join the server to the tailnet.
- Use a single-use, ephemeral, pre-authorized auth key that expires after one hour.
- All unspecified settings use Hetzner or provider defaults
- Hetzner Terraform files live in `infra/terraform/hcloud-server/`.
- Ansible inventory is generated at `infra/ansible/inventory.ini`

## Implementation Plan

1. Add the Hetzner Terraform provider and accept `HCLOUD_TOKEN` from the environment.
2. Read the user-generated public key from `~/.ssh/tiny-inference.pub` and upload it to Hetzner.
3. Use the matching private key at `~/.ssh/tiny-inference` for Ansible connections.
4. Create one `cax31` server in `hel1` using Ubuntu 24.04 and the generated SSH key.
5. Pass the short-lived Tailscale auth key to cloud-init and join the tailnet as `tiny-inference`.
6. Generate `infra/ansible/inventory.ini` with the Tailscale hostname, `root` user, and private-key path.
7. Output the server's public IPv4 and IPv6 addresses.
8. Attach a firewall that permits Tailscale UDP traffic and public FastAPI traffic on TCP port 8000, but no public SSH traffic.

## Acceptance Criteria

- `terraform apply` provisions the server and uploads the existing public key without manual console steps.
- `~/.ssh/tiny-inference` exists and has `0600` permissions before Terraform runs.
- The server joins the tailnet during cloud-init.
- The server is reachable through normal SSH over Tailscale using the generated key.
- Public SSH is not reachable.
- FastAPI is reachable from the public internet on TCP port 8000.
- `ansible all -i infra/ansible/inventory.ini -m ping` succeeds.
- No private key, Terraform state, token, or generated inventory is committed to Git.
- The auth key is sensitive but is present in both local Terraform states and the server's cloud-init user data.
