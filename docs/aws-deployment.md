# AWS deployment guide (EC2 + RDS + S3)

The Terraform folder is a starter infrastructure definition, not a command to run blindly. Creating EC2/RDS/S3 resources can incur AWS charges. Review region, instance sizes, CIDRs, backups, and estimated costs before applying.

## Suggested topology

- EC2 runs the FastAPI container, Celery worker, and Redis (or use managed ElastiCache for production).
- RDS MySQL is in private subnets; its security group accepts port 3306 only from the application EC2 security group.
- The app is exposed through an HTTPS load balancer or a reverse proxy with a real TLS certificate. Do not expose port 8000 directly to the public internet for production. Configure trusted proxy handling before relying on client IP rate limits behind a load balancer; do not blindly trust arbitrary `X-Forwarded-For` headers.
- S3 stores exported CSV reports. Enable block-public-access and default encryption.
- Store `SECRET_KEY`, DB credentials, and other secrets in AWS Systems Manager Parameter Store or Secrets Manager. Do not put secrets in Git or Terraform state.

## Deployment sequence

1. Create an AWS account and configure the AWS CLI with a least-privilege deployment identity.
2. Review `infra/terraform/variables.tf` and `infra/terraform/main.tf`; set `admin_cidr` to your own public IP `/32` or disable SSH in favour of Systems Manager Session Manager.
3. Run `terraform init`, `terraform validate`, and `terraform plan` in `infra/terraform`. Review every resource and cost before `terraform apply`.
4. Provision an RDS database and an EC2 host. Restrict the RDS security group to the app security group.
5. Install Docker Compose on EC2, clone the repository, and create a production `.env` from the example using secrets retrieved securely from Parameter Store/Secrets Manager.
6. Set `DATABASE_URL` to the RDS endpoint, `PUBLIC_BASE_URL` to your HTTPS domain, `ENVIRONMENT=production`, a strong `SECRET_KEY`, and a Redis URL reachable by API and worker.
7. Run `alembic upgrade head`, then start the API and worker containers. Configure a TLS reverse proxy / ALB and monitoring.
8. Verify `/health/live`, register/login, create a short URL, click it, and confirm the click appears in analytics after the worker processes it.
9. Export a CSV with `python scripts/export_analytics.py --from YYYY-MM-DD --to YYYY-MM-DD --s3` after setting `S3_BUCKET` and AWS credentials/role permissions.

## Security checklist

- Replace every development password and secret.
- Use HTTPS, private RDS subnets, restrictive security groups, and least-privilege IAM roles.
- Do not use `RATE_LIMIT_FAIL_OPEN=true` in a strict production environment; use `false` so Redis failure is visible instead of bypassing the distributed limiter.
- Add a domain allow/deny policy if this service will be public; shorteners can be abused for phishing and malware distribution.
- Enable RDS automated backups, CloudWatch logs/alarms, dependency updates, and a data-retention policy for click analytics.
- Consider AWS WAF and abuse reporting before accepting anonymous public traffic.
