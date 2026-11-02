output "ask_url" {
  description = "POST JSON {\"question\": \"...\"} to this URL."
  value       = "${aws_apigatewayv2_stage.default.invoke_url}ask"
}

output "lambda_function_name" {
  description = "Name of the orchestration Lambda function."
  value       = aws_lambda_function.ask.function_name
}

output "log_group_name" {
  description = "CloudWatch log group for the Lambda function."
  value       = aws_cloudwatch_log_group.ask.name
}
