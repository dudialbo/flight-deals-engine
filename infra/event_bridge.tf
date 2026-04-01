resource "aws_cloudwatch_event_rule" "every_six_hours" {
  name                = "${var.project_name}-hot-deals-trigger-${var.environment}"
  description         = "Trigger flight deals engine for hot deals every 6 hours"
  schedule_expression = "rate(6 hours)"
}

resource "aws_cloudwatch_event_target" "trigger_lambda_hot_deals" {
  rule      = aws_cloudwatch_event_rule.every_six_hours.name
  target_id = "EngineLambda"
  arn       = aws_lambda_function.engine_lambda.arn

  # Pass the jobType so the lambda handler knows what to execute
  input = jsonencode({
    "jobType" : "refresh_hot_deals"
  })
}

# Allow EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.engine_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_six_hours.arn
}
