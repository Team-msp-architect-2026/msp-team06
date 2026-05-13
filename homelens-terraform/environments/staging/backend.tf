terraform {
  backend "s3" {
    bucket         = "homelens-tfstate-staging"
    key            = "staging/terraform.tfstate"
    region         = "eu-west-3"
    dynamodb_table = "homelens-tfstate-lock"
    encrypt        = true
  }
}
