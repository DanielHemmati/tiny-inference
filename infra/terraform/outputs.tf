output "server_ipv4" {
  description = "Public IPv4 address of the server."
  value       = hcloud_server.tiny_inference.ipv4_address
}

output "server_ipv6" {
  description = "Public IPv6 address of the server."
  value       = hcloud_server.tiny_inference.ipv6_address
}
