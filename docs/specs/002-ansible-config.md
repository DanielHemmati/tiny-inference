# Server Init Configuration with Ansible

## Goal

Create a simple Ansible playbook that prepares the Ubuntu server for development by updating its APT packages and installing Python and `uv`.

## Requirements

- The playbook lives in `infra/ansible/` and uses the existing Ansible inventory.
- Target hosts run Ubuntu.
- Update the APT package cache and upgrade installed packages.
- Install the latest Python 3 version available from the configured Ubuntu repositories.
- Install the latest stable version of `uv`.
- The playbook must be safe to run more than once.

## Implementation Plan

1. Add an Ansible playbook for all hosts in the generated inventory.
2. Refresh the APT cache and upgrade installed packages using Ansible's APT module.
3. Install Python 3 using Ubuntu's package repositories.
4. Install `uv` using its official installation method and make it available on the command line.

## Acceptance Criteria

- Running the playbook against `infra/ansible/inventory.ini` completes successfully.
- The server's APT cache is current and installed packages are upgraded.
- `python3 --version` succeeds on the server.
- `uv --version` succeeds on the server.
- Running the playbook a second time completes without errors or unnecessary changes.

Status: ⬜
