# Ansible

Terraform generates `inventory.ini` in this directory after a successful apply.

Test the server from the repository root:

```bash
ansible all -i infra/ansible/inventory.ini -m ping
```
