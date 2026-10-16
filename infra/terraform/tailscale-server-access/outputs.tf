output "tailscale_auth_key" {
  description = "Single-use auth key used by cloud-init to register the ephemeral, untagged server."
  value       = tailscale_tailnet_key.server.key
  sensitive   = true
}
