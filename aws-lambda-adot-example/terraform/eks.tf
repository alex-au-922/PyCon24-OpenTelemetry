module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "${var.project_prefix}-eks-${var.env}"
  cluster_version = var.eks_config.cluster_version

  cluster_endpoint_public_access = true

  cluster_addons = {
    coredns                = {}
    eks-pod-identity-agent = {}
    aws-ebs-csi-driver     = {}
    kube-proxy             = {}
    vpc-cni                = {}
  }

  vpc_id     = module.vpc.vpc_id
  subnet_ids = flatten([module.vpc.public_subnets, module.vpc.private_subnets])

  # EKS Managed Node Group(s)
  eks_managed_node_group_defaults = {
    instance_types = var.eks_config.instance_types
    ami_type       = var.eks_config.ami_type
    min_size       = var.eks_config.min_size
    max_size       = var.eks_config.max_size
    desired_size   = var.eks_config.desired_size
  }

  eks_managed_node_groups = {
    public = {
      subnet_ids = module.vpc.public_subnets
      labels = {
        "nodegroup-type" = "public"
      }
    }

    private = {
      subnet_ids = module.vpc.private_subnets
      labels = {
        "nodegroup-type" = "private"
      }

    }
  }

  # Cluster access entry
  # To add the current caller identity as an administrator
  enable_cluster_creator_admin_permissions = true
}

resource "aws_security_group_rule" "eks" {
  for_each = module.eks.eks_managed_node_groups
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  source_security_group_id = aws_security_group.alb_security_group.id
  security_group_id = each.value.security_group_id
}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = "${base64decode(module.eks.cluster_certificate_authority_data)}"
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = "${base64decode(module.eks.cluster_certificate_authority_data)}"
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

module "eks_blueprints_addons" {
  source  = "aws-ia/eks-blueprints-addons/aws"
  version = "1.19.0"

  cluster_name      = module.eks.cluster_name
  cluster_endpoint  = module.eks.cluster_endpoint
  cluster_version   = module.eks.cluster_version
  oidc_provider_arn = module.eks.oidc_provider_arn



  enable_aws_load_balancer_controller = true
  enable_cluster_autoscaler           = true
  enable_metrics_server               = true
}

output "managed_node_group" {
  value = module.eks.eks_managed_node_groups
}

resource "kubernetes_namespace" "otel" {
  metadata {
    name = var.otel_config.namespace
  }
}

resource "helm_release" "otel" {
  name       = "otel"
  repository = var.otel_config.chart_repository
  chart      = var.otel_config.chart
  version    = var.otel_config.chart_version
  namespace = kubernetes_namespace.otel.metadata.0.name

  values = [
    "${file("${path.module}/manifests/otel.values.yaml.tftpl")}"
  ]
}

resource "kubernetes_manifest" "otel_tg_binding" {
  manifest = yamldecode(<<-EOF
  apiVersion: elbv2.k8s.aws/v1beta1
  kind: TargetGroupBinding
  metadata:
    name: otel-tg-binding
    namespace: ${var.otel_config.namespace}
  spec:
    serviceRef:
      name: ${helm_release.otel.name}-${helm_release.otel.chart}
      port: 4318
    targetGroupARN: ${aws_lb_target_group.otel_tg.arn}
  EOF
  )
}