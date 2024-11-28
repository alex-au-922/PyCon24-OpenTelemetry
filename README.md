# PyCon24-OpenTelemetry
This repository contains the source codes for the PyCon HK 2024 topic "Operate with Confidence -- OpenTelemetry in Python"

There are two parts in this repository:
1. [aws-lambda-adot-example](aws-lambda-adot-example): A simple AWS Lambda function that sends data to custom OTEL collector in EKS using AWS Distro for OpenTelemetry (ADOT) layer.
2. [grafana-otel-example](grafana-otel-example): A simple Grafana dashboard that visualizes a simplistic distributed microservices architecture, including binding logs (loki) and traces (tempo) together.

## aws-lambda-adot-example

### Introduction
[AWS Distro for OpenTelemetry](https://aws-otel.github.io/) is an AWS-supported OTEL distribution for AWS computes, especially on AWS Lambda.

With ADOT, we can add the ADOT layer as a [lambda extension](https://docs.aws.amazon.com/lambda/latest/dg/lambda-extensions.html) which runs **beyond the lifecycle of a lambda invocation**. The ADOT layer helps sending observability metrics towards our configured OTEL collector endpoint.

### Prerequisites
- [AWS Account](https://aws.amazon.com/): Setup AWS Lambda and OTEL in EKS
- [Terraform](https://developer.hashicorp.com/terraform/install): Use IaC (infrastructure as code) to guide the setup process
- Domain Name(Optional): Create a CNAME record to the AWS Application Load Balancer for DNS challenge and TLS cert
- AWS S3 Bucket for Terraform state storage (Optional): If opt-out this feature, comment out the whole `aws-lambda-adot-example/terraform/backend.tf` file.

### Architecture Diagram
![Architecture Diagram](aws-lambda-adot-example/docs/architecture-diagram.png)

### Installation
Run the following command:
```
$ cd aws-lambda-adot-example/terraform
$ terraform init
$ terraform plan -out aws.tfplan
$ terraform apply aws.tfplan
```

### Testing
You can simply test the behavior by sending test events to lambda via the AWS Lambda test events page.

