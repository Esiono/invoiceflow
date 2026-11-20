output "account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "state_bucket" {
  value = aws_s3_bucket.tfstate.bucket
}

output "budget_name" {
  value = aws_budgets_budget.monthly_total.name
}
