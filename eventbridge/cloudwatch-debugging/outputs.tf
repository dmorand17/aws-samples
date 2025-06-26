
# Output the EventBridge Rule ARN
output "eventbridge_rule_arn" {
  value = aws_cloudwatch_event_rule.all_events.arn
}

# Output the CloudWatch Log Group ARN
output "cloudwatch_log_group_arn" {
  value = aws_cloudwatch_log_group.events_log_group.arn
}

output "backend_config" {
  value = module.terraform_state.backend_config
}
