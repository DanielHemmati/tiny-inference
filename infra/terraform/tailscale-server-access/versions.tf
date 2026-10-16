terraform {
  required_version = ">= 1.10.0"

  required_providers {
    tailscale = {
      source  = "tailscale/tailscale"
      version = "~> 0.29"
    }
  }
}

provider "tailscale" {}
