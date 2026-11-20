terraform {
  required_version = ">= 1.11.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0" # exact version pinned in .terraform.lock.hcl (commit it)
    }
  }
  # Local state on purpose: this stack creates the remote-state bucket itself.
}
