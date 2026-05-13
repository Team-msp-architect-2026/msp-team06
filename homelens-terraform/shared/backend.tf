terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = ">= 4.0.0"
    }
  }

  backend "s3" {
    bucket         = "homelens-tfstate-prod"
    key            = "shared/terraform.tfstate"
    region         = "eu-west-3"
    dynamodb_table = "homelens-tfstate-lock"
    encrypt        = true
  }
}
