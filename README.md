# PyCon24-OpenTelemetry
This repository contains the source codes for the PyCon HK 2024 topic "Operate with Confidence -- OpenTelemetry in Python"

There are two parts in this repository:
1. [aws-lambda-adot-example](aws-lambda-adot-example): A simple AWS Lambda function that sends data to custom OTEL collector in EKS using AWS Distro for OpenTelemetry (ADOT) layer.
2. [grafana-otel-example](grafana-otel-example): A simple Grafana dashboard that visualizes a simplistic distributed microservices architecture, including binding logs (loki) and traces (tempo) together.

## Relevant Materials
- [PyCon HK 2024 Slides](https://1drv.ms/p/c/40f756128322ebe1/EQRjw4ZYfbRAn8bnRewOglQBUiRICmsVz0oAZUWMDKC7Pg)

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
![Architecture Diagram](https://github.com/alex-au-922/PyCon24-OpenTelemetry/blob/main/aws-lambda-adot-example/doc/architecture_diagram.drawio.png)

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

## grafana-otel-example

### Introduction
Normally, we use Grafana to visualize metrics and logs. With the help of OpenTelemetry, we can easily export metrics, logs, and traces to Prometheus, Loki, and Tempo, respectively. Grafana can then visualize these data sources in a single dashboard.

By setting up **auto-instrumentation** in the Python application, we can easily export metrics, logs, and traces with metrics and logs added **trace ids and span ids automatically**. This helps us to trace the logs and metrics in a distributed system.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/): Run the Grafana, Loki, and Tempo services in containers

### Architecture Diagram
![Architecture Diagram](https://github.com/alex-au-922/PyCon24-OpenTelemetry/blob/main/grafana-otel-example/doc/architecture_diagram.drawio.png)

### Installation
Run the following command:
```
$ cd grafana-otel-example/terraform
$ docker compose up -d
```

### Testing
You can run the following script to generate fake traffics:
```
$ cd grafana-otel-example
$ python3 traffic_generator.py
```

Then you can access the Grafana dashboard at `http://localhost:3000`.
