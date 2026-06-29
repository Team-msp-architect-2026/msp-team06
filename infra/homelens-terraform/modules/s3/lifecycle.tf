resource "aws_s3_bucket_lifecycle_configuration" "raw_data" {
    bucket = aws_s3_bucket.raw_data.id

    rule {
      id    = "archive-molit-raw"
      status = "Enabled"
      filter { prefix = "molit/" }
      transition {
        days          = var.glacier_transition_days
        storage_class = "GLACIER"
      }
    }
}
