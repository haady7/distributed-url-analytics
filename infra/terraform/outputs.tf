output "app_public_ip" {
  value       = aws_instance.app.public_ip
  description = "EC2 public IP. Configure DNS and HTTPS before production use."
}

output "rds_endpoint" {
  value       = aws_db_instance.main.address
  description = "Private RDS endpoint; reachable only from the application security group."
}

output "analytics_bucket" {
  value       = aws_s3_bucket.analytics.bucket
  description = "Private S3 bucket for CSV analytics exports."
}
