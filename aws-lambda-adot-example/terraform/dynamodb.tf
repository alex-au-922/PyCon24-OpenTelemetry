module "product_info_dynamodb_table" {
  source  = "terraform-aws-modules/dynamodb-table/aws"
  version = "4.2.0"

  name     = var.dynamodb_config.table_name
  hash_key = var.dynamodb_config.hash_key

  attributes = [
    {
      name = var.dynamodb_config.hash_key
      type = var.dynamodb_config.hash_key_type
    }
  ]
  billing_mode   = "PROVISIONED"
  read_capacity  = var.dynamodb_config.read_capacity
  write_capacity = var.dynamodb_config.write_capacity
}