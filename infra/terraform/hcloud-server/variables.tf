variable "tailscale_auth_key" {
  description = "Short-lived auth key used by cloud-init to join the server to the tailnet."
  type        = string
  sensitive   = true
}
