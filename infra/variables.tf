variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project used for naming resources"
  type        = string
  default     = "flight-deals"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

variable "search_backend_base_url" {
  description = "Base URL for the search backend"
  type        = string
}

variable "search_backend_api_key" {
  description = "API key for the search backend (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "log_level" {
  description = "Logging level for the application"
  type        = string
  default     = "INFO"
}

variable "lambda_image_uri" {
  description = "ECR URI of the Docker image to deploy for the Lambda function"
  type        = string
}
