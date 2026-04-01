resource "aws_lambda_function" "engine_lambda" {
  function_name = "${var.project_name}-engine-${var.environment}"
  role          = aws_iam_role.lambda_exec_role.arn
  package_type  = "Image"
  image_uri     = var.lambda_image_uri
  timeout       = 300 # 5 minutes timeout
  memory_size   = 256

  environment {
    variables = {
      STORAGE_ADAPTER         = "s3"
      S3_BUCKET_NAME          = aws_s3_bucket.data_bucket.id
      SEARCH_BACKEND_BASE_URL = var.search_backend_base_url
      SEARCH_BACKEND_API_KEY  = var.search_backend_api_key
      LOG_LEVEL               = var.log_level
    }
  }
}
