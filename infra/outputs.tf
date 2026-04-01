output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.engine_lambda.function_name
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket where data is stored"
  value       = aws_s3_bucket.data_bucket.id
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule triggering the hot deals job"
  value       = aws_cloudwatch_event_rule.every_six_hours.name
}
