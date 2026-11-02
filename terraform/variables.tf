variable "aws_region" {
  description = "AWS region for the Lambda function and HTTP API."
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Name prefix for every resource."
  type        = string
  default     = "biomecha-rag"
}

variable "lambda_zip_path" {
  description = "Path to the Lambda deployment package (code plus dependencies plus bm25_params.json)."
  type        = string
  default     = "../build/lambda.zip"
}

variable "hf_token_ssm_name" {
  description = "Name of the SecureString SSM parameter that holds the Hugging Face token."
  type        = string
  default     = "/biomecha-rag/hf-token"
}

variable "pinecone_api_key_ssm_name" {
  description = "Name of the SecureString SSM parameter that holds the Pinecone API key."
  type        = string
  default     = "/biomecha-rag/pinecone-api-key"
}

variable "embed_endpoint_url" {
  description = "Hugging Face Inference Endpoint URL serving the BGE embedding model."
  type        = string
}

variable "rerank_endpoint_url" {
  description = "Hugging Face Inference Endpoint URL serving the BGE cross-encoder reranker."
  type        = string
}

variable "llm_endpoint_url" {
  description = "Hugging Face Inference Endpoint URL serving Mistral-7B-Instruct."
  type        = string
}

variable "pinecone_index" {
  description = "Pinecone index name. The index must use the dotproduct metric."
  type        = string
  default     = "biomecha-rag"
}

variable "pinecone_namespace" {
  description = "Pinecone namespace for the corpus."
  type        = string
  default     = "sports-science"
}

variable "hybrid_alpha" {
  description = "Dense weight in the hybrid score. The sparse weight is 1 minus alpha."
  type        = number
  default     = 0.5

  validation {
    condition     = var.hybrid_alpha >= 0 && var.hybrid_alpha <= 1
    error_message = "hybrid_alpha must be between 0 and 1."
  }
}

variable "lambda_timeout_seconds" {
  description = "Lambda timeout. HTTP API integrations stop waiting after 30 seconds."
  type        = number
  default     = 29
}

variable "lambda_memory_mb" {
  description = "Lambda memory size in MB."
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 14
}

variable "throttle_rate_limit" {
  description = "Steady-state requests per second allowed by the API stage."
  type        = number
  default     = 5
}

variable "throttle_burst_limit" {
  description = "Burst requests allowed by the API stage."
  type        = number
  default     = 10
}
