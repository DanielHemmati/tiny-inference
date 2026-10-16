HCLOUD_TF_DIR := infra/terraform/hcloud-server
TAILSCALE_TF_DIR := infra/terraform/tailscale-server-access
HCLOUD_TF := terraform -chdir=$(HCLOUD_TF_DIR)
TAILSCALE_TF := terraform -chdir=$(TAILSCALE_TF_DIR)
ANSIBLE_DIR := infra/ansible
ANSIBLE_CONFIG := $(CURDIR)/$(ANSIBLE_DIR)/ansible.cfg

-include .env
export HCLOUD_TOKEN TAILSCALE_API_KEY TAILSCALE_TAILNET

.DEFAULT_GOAL := help

.PHONY: help init fmt validate plan apply configure destroy output ssh-root ssh-tiny

help:
	@echo "Available commands:"
	@echo "  make init                         Initialize both Terraform roots"
	@echo "  make fmt                          Format both Terraform roots"
	@echo "  make validate                     Validate both Terraform roots"
	@echo "  make plan                         Preview both Terraform roots"
	@echo "  make apply                        Apply Tailscale and Hetzner resources"
	@echo "  make apply ARGS=-auto-approve     Apply without confirmation"
	@echo "  make configure                    Configure the server with Ansible"
	@echo "  make output                       Show both Terraform roots' outputs"
	@echo "  make ssh-root                     Connect privately as root over Tailscale"
	@echo "  make ssh-tiny                     Connect privately as tiny-inference over Tailscale"
	@echo "  make destroy                      Destroy Hetzner and Tailscale resources"

init:
	$(HCLOUD_TF) init
	$(TAILSCALE_TF) init

fmt:
	$(HCLOUD_TF) fmt
	$(TAILSCALE_TF) fmt

validate: init
	$(HCLOUD_TF) validate
	$(TAILSCALE_TF) validate

plan: validate
	$(TAILSCALE_TF) plan
	@tailscale_auth_key="$$($(TAILSCALE_TF) output -raw tailscale_auth_key 2>/dev/null || true)"; \
		if [ -z "$$tailscale_auth_key" ]; then tailscale_auth_key=tskey-auth-plan-placeholder; fi; \
		TF_VAR_tailscale_auth_key="$$tailscale_auth_key" $(HCLOUD_TF) plan

apply: validate
	$(TAILSCALE_TF) apply $(ARGS)
	@TF_VAR_tailscale_auth_key="$$($(TAILSCALE_TF) output -raw tailscale_auth_key)" \
		$(HCLOUD_TF) apply $(ARGS)

configure:
	ANSIBLE_CONFIG=$(ANSIBLE_CONFIG) ansible-playbook $(ANSIBLE_DIR)/playbook.yml

destroy: init
	@tailscale_auth_key="$$($(TAILSCALE_TF) output -raw tailscale_auth_key 2>/dev/null || true)"; \
		if [ -z "$$tailscale_auth_key" ]; then tailscale_auth_key=tskey-auth-destroy-placeholder; fi; \
		TF_VAR_tailscale_auth_key="$$tailscale_auth_key" $(HCLOUD_TF) destroy
	$(TAILSCALE_TF) destroy

output:
	$(HCLOUD_TF) output
	$(TAILSCALE_TF) output

ssh-root:
	ssh -i $(HOME)/.ssh/tiny-inference -o StrictHostKeyChecking=accept-new root@tiny-inference

ssh-tiny:
	ssh -i $(HOME)/.ssh/tiny-inference -o StrictHostKeyChecking=accept-new tiny-inference@tiny-inference
