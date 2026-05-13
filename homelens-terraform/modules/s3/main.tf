resource "aws_s3_bucket" "raw_data" {
    bucket = "${var.project_name}-${var.env}-raw-data"
    tags   = { Env = var.env, Purpose = "raw-data-ingest" }
}

resource "aws_s3_bucket_public_access_block" "raw_data" {
    bucket                  = aws_s3_bucket.raw_data.id
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}

resource "aws_s3_bucket" "report_backup" {
    bucket = "${var.project_name}-${var.env}-report-backup"
    tags   = { Env = var.env, Purpose = "report-backup" }
}

resource "aws_s3_bucket_public_access_block" "report_backup" {
    bucket                  = aws_s3_bucket.report_backup.id
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}
