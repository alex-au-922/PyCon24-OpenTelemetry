data "aws_route53_zone" "this" {
  name         = "${var.hosted_zone_config.name}."
  private_zone = false
}

resource "aws_acm_certificate" "this" {
  domain_name       = data.aws_route53_zone.this.name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.hosted_zone_config.name}"
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# Create Route 53 records for ACM certificate validation
resource "aws_route53_record" "validation" {
  for_each = {
    for dvo in aws_acm_certificate.this.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  }

  zone_id = data.aws_route53_zone.this.zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.record]
}

resource "aws_lb" "this" {
  name               = "${var.project_prefix}-alb-${var.env}"
  load_balancer_type = "application"
  internal           = false

  security_groups = [aws_security_group.alb_security_group.id]
  subnets         = module.vpc.public_subnets
  idle_timeout    = 300

}

resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.this.arn
  protocol          = "HTTP"
  port              = "80"
  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}


resource "aws_lb_listener" "https_listener" {
  load_balancer_arn = aws_lb.this.arn
  protocol          = "HTTPS"
  port              = "443"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.this.arn
  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }
}

resource "aws_lb_listener_rule" "otel_listener" {
  listener_arn = aws_lb_listener.https_listener.arn
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.otel_tg.arn
  }
  condition {
    host_header {
      values = ["otel.${var.hosted_zone_config.name}"]
    }
  }
}


resource "aws_lb_target_group" "otel_tg" {
  name        = "otel-tg"
  port        = "4318"
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = module.vpc.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 4
    unhealthy_threshold = 4
    interval            = 15

    protocol = "HTTP"
    port     = "13133"
    matcher  = "200"
    path     = "/"
  }
}

resource "aws_route53_record" "dns" {
  for_each = toset(var.hosted_zone_config.fqdn_prefixes)
  zone_id  = data.aws_route53_zone.this.zone_id
  name     = "${each.key}.${var.hosted_zone_config.name}"
  type     = "CNAME"
  ttl      = 60
  records  = [aws_lb.this.dns_name]
}
