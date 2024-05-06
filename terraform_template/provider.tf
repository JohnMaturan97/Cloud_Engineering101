terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  cloud {
    organization = "Andromeda101"

    workspaces {
      name = "aws-andromeda-slvr"
    }
  }
}

provider "aws" {
  region     = "us-east-1"
  access_key = var.Access_Key_ID
  secret_key = var.Secret_Access_Key
}
