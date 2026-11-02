resource "aws_cloudwatch_log_group" "ask" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days
}

data "aws_iam_policy_document" "assume_lambda" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ask" {
  name               = "${local.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

# Least privilege: write to its own log group and read two named parameters.
data "aws_iam_policy_document" "ask" {
  statement {
    sid       = "WriteOwnLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.ask.arn}:*"]
  }

  statement {
    sid       = "ReadNamedSecrets"
    actions   = ["ssm:GetParameter"]
    resources = local.ssm_parameter_arns
  }
}

resource "aws_iam_role_policy" "ask" {
  name   = "${local.function_name}-policy"
  role   = aws_iam_role.ask.id
  policy = data.aws_iam_policy_document.ask.json
}

resource "aws_lambda_function" "ask" {
  function_name    = local.function_name
  role             = aws_iam_role.ask.arn
  runtime          = "python3.12"
  handler          = "biomecha_rag.handler.lambda_handler"
  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)
  timeout          = var.lambda_timeout_seconds
  memory_size      = var.lambda_memory_mb
  architectures    = ["x86_64"]

  environment {
    variables = {
      HF_TOKEN_SSM_PARAM         = var.hf_token_ssm_name
      PINECONE_API_KEY_SSM_PARAM = var.pinecone_api_key_ssm_name
      EMBED_ENDPOINT_URL         = var.embed_endpoint_url
      RERANK_ENDPOINT_URL        = var.rerank_endpoint_url
      LLM_ENDPOINT_URL           = var.llm_endpoint_url
      PINECONE_INDEX             = var.pinecone_index
      PINECONE_NAMESPACE         = var.pinecone_namespace
      HYBRID_ALPHA               = tostring(var.hybrid_alpha)
      BM25_PARAMS_PATH           = "bm25_params.json"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.ask,
    aws_iam_role_policy.ask,
  ]
}
