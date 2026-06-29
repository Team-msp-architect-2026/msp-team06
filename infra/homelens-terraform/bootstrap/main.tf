terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
      Component = "bootstrap"
    }
  }
}

# ---------------------------------------------------------------------------
# S3 — tfstate 버킷 (dev / staging / prod 각각)
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "tfstate" {
  for_each = toset(var.environments)

  bucket        = "${var.project_name}-tfstate-${each.key}"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "tfstate" {
  for_each = aws_s3_bucket.tfstate

  bucket = each.value.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  for_each = aws_s3_bucket.tfstate

  bucket = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  for_each = aws_s3_bucket.tfstate

  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "tfstate" {
  for_each = aws_s3_bucket.tfstate

  bucket = each.value.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  depends_on = [aws_s3_bucket_versioning.tfstate]
}

# ---------------------------------------------------------------------------
# DynamoDB — state lock 테이블 (전 환경 공용 1개)
# ---------------------------------------------------------------------------
resource "aws_dynamodb_table" "tfstate_lock" {
  name         = "${var.project_name}-tfstate-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
