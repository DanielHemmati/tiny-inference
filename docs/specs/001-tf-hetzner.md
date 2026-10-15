# Create a Hetzner Server with Terraform

## Goal

Provision one cost-optimized ARM64 server on Hetzner Cloud and generate an Ansible inventory for it.

## Requirements

- Location: Helsinki (`hel1`)
- Server type: `cax31` (ARM64, 8 vCPU, 16 GB RAM)
- OS: Ubuntu 24.04 LTS
- Networking: default public IPv4 and IPv6 only
- All unspecified settings use Hetzner or provider defaults
- Terraform files live in `infra/terraform/`
- Ansible inventory is generated at `infra/ansible/inventory.ini`

## Implementation Plan

1. Add the Hetzner Terraform provider and accept `HCLOUD_TOKEN` from the environment.
2. Read the user-generated public key from `~/.ssh/tiny-inference.pub` and upload it to Hetzner.
3. Use the matching private key at `~/.ssh/tiny-inference` for Ansible connections.
4. Create one `cax31` server in `hel1` using Ubuntu 24.04 and the generated SSH key.
5. Generate `infra/ansible/inventory.ini` with the server's public IPv4 address, `root` user, and private-key path.
6. Output the server's public IPv4 and IPv6 addresses.

## Acceptance Criteria

- `terraform apply` provisions the server and uploads the existing public key without manual console steps.
- `~/.ssh/tiny-inference` exists and has `0600` permissions before Terraform runs.
- The server is reachable over SSH using the generated key.
- `ansible all -i infra/ansible/inventory.ini -m ping` succeeds.
- No private key, Terraform state, token, or generated inventory is committed to Git.

Status: ✅
