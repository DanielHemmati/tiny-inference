TF_DIR := infra/terraform
TF := terraform -chdir=$(TF_DIR)
ANSIBLE_DIR := infra/ansible
ANSIBLE_CONFIG := $(CURDIR)/$(ANSIBLE_DIR)/ansible.cfg

.DEFAULT_GOAL := help

.PHONY: help init fmt validate plan apply configure destroy output ssh

help:
	@echo "Available commands:"
	@echo "  make init                         Initialize Terraform"
	@echo "  make fmt                          Format Terraform files"
	@echo "  make validate                     Validate the configuration"
	@echo "  make plan                         Preview infrastructure changes"
	@echo "  make apply                        Apply changes interactively"
	@echo "  make apply ARGS=-auto-approve     Apply without confirmation"
	@echo "  make configure                    Configure the server with Ansible"
	@echo "  make output                       Show Terraform outputs"
	@echo "  make ssh-root                     Connect to the server as root"
	@echo "  make ssh-tiny                     Connect to the server as tiny-inference user"
	@echo "  make destroy                      Destroy the infrastructure"

init:
	$(TF) init

fmt:
	$(TF) fmt

validate: init
	$(TF) validate

plan: validate
	$(TF) plan

apply: validate
	$(TF) apply $(ARGS)

configure:
	ANSIBLE_CONFIG=$(ANSIBLE_CONFIG) ansible-playbook $(ANSIBLE_DIR)/playbook.yml

destroy: init
	$(TF) destroy

output:
	$(TF) output

ssh-root:
	ssh -i $(HOME)/.ssh/tiny-inference -o StrictHostKeyChecking=accept-new root@$$($(TF) output -raw server_ipv4)

ssh-tiny:
	ssh -i $(HOME)/.ssh/tiny-inference -o StrictHostKeyChecking=accept-new tiny-inference@$$($(TF) output -raw server_ipv4)
