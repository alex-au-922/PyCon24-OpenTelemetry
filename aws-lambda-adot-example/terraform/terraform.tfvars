project_prefix = "pyconhk-2024"
region         = "ap-southeast-1"
env            = "dev"

vpc_config = {
  cidr            = "10.0.0.0/16"
  azs             = ["ap-southeast-1a", "ap-southeast-1b", "ap-southeast-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

}

lambda_config = {
  src_path_parts                 = ["..", "lambda", "src"]
  timeout                        = 60 * 5
  memory_size                    = 1024
  reserved_concurrent_executions = 10
  architecture                   = "arm64"
  runtime                        = "python3.11"
  handler                        = "main.lambda_handler"
  log_retention_days             = 7

}

dynamodb_config = {
  table_name     = "product_info"
  hash_key       = "product_id"
  hash_key_type  = "S"
  read_capacity  = 10
  write_capacity = 10
}

eks_config = {
  cluster_version = "1.31"
  ami_type        = "AL2023_ARM_64_STANDARD"
  min_size        = 2
  max_size        = 4
  desired_size    = 3
  instance_types  = ["m6g.large"]
}

hosted_zone_config = {
  name = "<your_domain_name>"
  fqdn_prefixes = [
    "otel"
  ]
}

otel_config = {
  chart_version = "0.109.0"
  chart_repository = "https://open-telemetry.github.io/opentelemetry-helm-charts"
  chart = "opentelemetry-collector"
  namespace = "otel"
}