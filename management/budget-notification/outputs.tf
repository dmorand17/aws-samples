output "sns_topic_arn" {
  description = "The ARN of the SNS topic for budget alerts"
  value       = aws_sns_topic.budget_alerts.arn
}

output "budget_name" {
  description = "The name of the created budget"
  value       = aws_budgets_budget.monthly_budget.name
}

output "budget_id" {
  description = "The ID of the created budget."
  value       = aws_budgets_budget.monthly_budget.id
}
