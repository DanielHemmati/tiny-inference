resource "tailscale_tailnet_key" "server" {
  description   = "Tiny inference server"
  reusable      = false
  ephemeral     = true
  preauthorized = true
  expiry        = 3600
}
