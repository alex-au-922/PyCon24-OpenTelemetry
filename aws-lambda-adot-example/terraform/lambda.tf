locals {
  labmda_default_policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
  ]
}

#######################################################################
# Product Info Querier Lambda
#######################################################################

module "product_info_querier_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.14.0"

  function_name = "${var.project_prefix}-product-info-querier-${var.env}"
  handler       = var.lambda_config.handler
  runtime       = var.lambda_config.runtime
  architectures = [var.lambda_config.architecture]
  publish       = true

  timeout                        = var.lambda_config.timeout
  memory_size                    = var.lambda_config.memory_size

  package_type = "Zip"
  source_path  = join("/", var.lambda_config.src_path_parts)
  layers = [
    "arn:aws:lambda:${var.region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-${replace(var.lambda_config.runtime, ".", "")}-arm64:4",
    "arn:aws:lambda:${var.region}:901920570463:layer:aws-otel-python-${var.lambda_config.architecture}-ver-1-25-0:1"
  ]

  environment_variables = {
    DYNAMODB_TABLE_NAME = module.product_info_dynamodb_table.dynamodb_table_name
    DELAY_INJECTION_ENABLED = true
    FAULT_INJECTION_ENABLED = true
    AWS_LAMBDA_EXEC_WRAPPER = "/opt/otel-instrument"
    OTEL_METRICS_EXPORTER = "otlp"
    OTEL_TRACES_EXPORTER = "otlp"
    OTEL_LOGS_EXPORTER = "otlp"
    OTEL_EXPORTER_OTLP_TRACES_PROTOCOL = "http"
    OTEL_EXPORTER_OTLP_METRICS_PROTOCOL = "http"
    OTEL_EXPORTER_OTLP_LOGS_PROTOCOL = "http"
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = "otel.${var.hosted_zone_config.name}:4318/v1/traces"
    OTEL_EXPORTER_OTLP_METRICS_ENDPOINT = "otel.${var.hosted_zone_config.name}:4318/v1/metrics"
    OTEL_EXPORTER_OTLP_LOGS_ENDPOINT = "otel.${var.hosted_zone_config.name}:4318/v1/logs"
  }

  create_role                       = true
  attach_cloudwatch_logs_policy     = false
  cloudwatch_logs_retention_in_days = var.lambda_config.log_retention_days

  attach_policies          = true
  number_of_policies       = length(local.labmda_default_policies)
  policies                 = local.labmda_default_policies
  attach_policy_statements = true
  policy_statements = {
    dynamodb = {
      effect = "Allow",
      actions = [
        "dynamodb:*",
      ],
      resources = [
        module.product_info_dynamodb_table.dynamodb_table_arn
      ]
    },
  }

  vpc_security_group_ids = [aws_security_group.lambda_security_group.id]
  vpc_subnet_ids         = module.vpc.private_subnets
  attach_network_policy  = true
}
