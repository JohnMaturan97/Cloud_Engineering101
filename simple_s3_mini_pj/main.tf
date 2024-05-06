resource "aws_s3_bucket" "simple-jack-bucket" {
  bucket = var.bucketname
}

resource "aws_s3_bucket_ownership_controls" "s3_own_control" {
  bucket = aws_s3_bucket.simple-jack-bucket.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "s3_public_acess" {
  bucket = aws_s3_bucket.simple-jack-bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "s3_acl" {
  depends_on = [
    aws_s3_bucket_ownership_controls.s3_own_control,
    aws_s3_bucket_public_access_block.s3_public_acess,
  ]

  bucket = aws_s3_bucket.simple-jack-bucket.id
  acl    = "public-read"
}

resource "aws_s3_object" "index" {
  bucket       = aws_s3_bucket.simple-jack-bucket.id
  key          = "index.html"
  source       = "index.html"
  acl          = "public-read"
  content_type = "text/html"
  depends_on   = [aws_s3_bucket_acl.s3_acl]
}

resource "aws_s3_object" "error" {
  bucket       = aws_s3_bucket.simple-jack-bucket.id
  key          = "error_page.html"
  source       = "error_page.html"
  acl          = "public-read"
  content_type = "text/html"
  depends_on   = [aws_s3_bucket_acl.s3_acl]
}

resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.simple-jack-bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error_page.html"
  }
  depends_on = [aws_s3_bucket_acl.s3_acl]
}
