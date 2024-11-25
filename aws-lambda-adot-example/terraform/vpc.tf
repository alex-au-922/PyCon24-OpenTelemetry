resource "aws_eip" "nat" {
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.15.0"

  name = "${var.project_prefix}-vpc-${var.env}"
  cidr = var.vpc_config.cidr

  azs             = var.vpc_config.azs
  private_subnets = var.vpc_config.private_subnets
  public_subnets  = var.vpc_config.public_subnets

  enable_nat_gateway = true
  enable_vpn_gateway = true

  single_nat_gateway      = true
  reuse_nat_ips           = true
  external_nat_ip_ids     = aws_eip.nat.*.id
  map_public_ip_on_launch = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
}

resource "aws_security_group" "alb_security_group" {
  name        = "alb-security-group"
  description = "Security group for ALB"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "Allow all access from external"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "lambda_security_group" {
  name        = "lambda-security-group"
  description = "Security group for Lambda"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "Allow all access from VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = concat([module.vpc.vpc_cidr_block], module.vpc.vpc_secondary_cidr_blocks)
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}