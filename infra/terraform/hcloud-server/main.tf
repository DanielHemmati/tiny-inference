locals {
  ssh_private_key_path = pathexpand("~/.ssh/tiny-inference")
  ssh_public_key_path  = pathexpand("~/.ssh/tiny-inference.pub")
}

data "local_file" "ssh_public_key" {
  filename = local.ssh_public_key_path
}

resource "hcloud_ssh_key" "tiny_inference" {
  name       = "tiny-inference"
  public_key = trimspace(data.local_file.ssh_public_key.content)
}

resource "hcloud_server" "tiny_inference" {
  name        = "tiny-inference"
  location    = "hel1"
  server_type = "cax31"
  image       = "ubuntu-24.04"
  ssh_keys    = [hcloud_ssh_key.tiny_inference.id]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }
}

resource "local_file" "ansible_inventory" {
  filename             = "${path.module}/../../ansible/inventory.ini"
  file_permission      = "0644"
  directory_permission = "0755"

  content = <<-EOT
    [tiny_inference]
    tiny-inference ansible_host=${hcloud_server.tiny_inference.ipv4_address} 

    [tiny_inference:vars]
    ansible_user=root 
    ansible_ssh_private_key_file=${local.ssh_private_key_path} 
    ansible_ssh_common_args='-o StrictHostKeyChecking=accept-new'
  EOT
}
