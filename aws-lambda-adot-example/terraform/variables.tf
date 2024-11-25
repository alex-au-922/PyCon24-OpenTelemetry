variable "project_prefix" {
  type = string

}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

variable "vpc_config" {
  type = object({
    cidr            = string
    azs             = list(string)
    private_subnets = list(string)
    public_subnets  = list(string)
  })
}

variable "lambda_config" {
  type = object({
    src_path_parts                 = list(string)
    timeout                        = number
    memory_size                    = number
    reserved_concurrent_executions = number
    architecture                   = string
    runtime                        = string
    handler                        = string
    log_retention_days             = number
  })
}

variable "dynamodb_config" {
  type = object({
    table_name     = string
    hash_key       = string
    hash_key_type  = string
    read_capacity  = number
    write_capacity = number
  })
}

variable "eks_config" {
  type = object({
    cluster_version = string
    ami_type = string
    min_size        = number
    max_size        = number
    desired_size    = number
    instance_types  = list(string)
  })
}

variable "hosted_zone_config" {
  type = object({
    name          = string
    fqdn_prefixes = list(string)
  })
}

variable "otel_config" {
  type = object({
    chart_version    = string
    chart_repository = string
    chart            = string
    namespace        = string
  })
}