# Variables set when using module
variable "location" {}
variable "storage_name" {}
variable "network_name" {}
variable "subnet_name" {}
variable "vm_image" {}
variable "vm_size" {}
variable "ssh_username" {}
variable "ssh_password" {}
variable "domain" {}

# DNS Records
variable "dns_master_internal" { 
  description = "DNS A record pointing to the internal IP of the master"
  default = "master" 
}

variable "dns_master_external" { 
  description = "DNS A record pointing to the external IP of the master"
  default = "master-ext"
}