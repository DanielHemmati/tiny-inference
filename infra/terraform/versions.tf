terraform {
  required_version = ">= 1.10.0"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.50"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

# INFO: I am using .env so i can also use `hcloud` cli as well
# Not a good practice but it's okay in my case
provider "hcloud" {}
