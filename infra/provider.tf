terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  backend "s3" {
    bucket = "dudialbo-aws-terraform-state"
    key    = "flight-deals-engine/prod/terraform.tfstate"
    region = "us-east-1"

    use_lockfile = true
    encrypt      = true

    profile = "bootstrap"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "flight-deals-engine"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
