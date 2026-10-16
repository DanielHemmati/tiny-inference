# Ansible

Terraform generates `inventory.ini` in this directory after a successful apply.

Copy `.env.example` to `.env` and set the Hetzner token and a Tailscale API key.
The Tailscale API key must be allowed to create auth keys. `make` loads these
credentials without storing them in Terraform configuration files.

Cloud-init installs Tailscale and joins the server to the tailnet. Your local
computer must be connected to the same tailnet before you run Ansible:

```bash
make apply
make configure
```

Test the server from the repository root:

```bash
ansible all -i infra/ansible/inventory.ini -m ping
```

The inventory and Make targets use normal SSH over the private Tailscale
hostname:

```bash
make ssh-tiny
```
