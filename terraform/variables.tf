variable "prefix" {
  type        = string
  description = "Short lowercase name used to build resource names"
  default     = "k8slearn"
}

variable "location" {
  type    = string
  default = "uksouth"
}

variable "node_vm_size" {
  type        = string
  description = "Check this size is available to your subscription in the chosen region"
  default     = "Standard_B2s"
}
