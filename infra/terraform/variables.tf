variable "aws_region" {
  description = "AWS region in which to create resources."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Short project prefix used for resource names."
  type        = string
  default     = "linkpulse"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.20.1.0/24"
}

variable "private_db_subnet_cidrs" {
  type    = list(string)
  default = ["10.20.10.0/24", "10.20.11.0/24"]

  validation {
    condition     = length(var.private_db_subnet_cidrs) >= 2
    error_message = "RDS DB subnet groups require at least two private subnets."
  }
}

variable "admin_cidr" {
  description = "Your public IPv4 CIDR for SSH, e.g. 203.0.113.10/32. Do not use 0.0.0.0/0."
  type        = string
  default     = "127.0.0.1/32"
  sensitive   = false
}

variable "key_name" {
  description = "Existing EC2 key pair name. Leave empty to use Systems Manager Session Manager only."
  type        = string
  default     = ""
}

variable "ec2_instance_type" {
  type    = string
  default = "t3.micro"
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_name" {
  type    = string
  default = "linkpulse"
}

variable "db_username" {
  type    = string
  default = "linkpulse_admin"
}

variable "db_password" {
  description = "Temporary bootstrap password. Prefer Secrets Manager in a production deployment; Terraform state contains sensitive values."
  type        = string
  sensitive   = true
}
