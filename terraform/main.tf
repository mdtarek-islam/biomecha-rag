provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  function_name = "${var.project_name}-ask"

  # Parameter ARNs built from names. Terraform never reads the secret values.
  ssm_parameter_arns = [
    for name in [var.hf_token_ssm_name, var.pinecone_api_key_ssm_name] :
    "arn:${data.aws_partition.current.partition}:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${trimprefix(name, "/")}"
  ]
}
