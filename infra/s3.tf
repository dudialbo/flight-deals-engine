resource "aws_s3_bucket" "data_bucket" {
  bucket        = "${var.project_name}-data-${var.environment}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "data_bucket_pab" {
  bucket = aws_s3_bucket.data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
