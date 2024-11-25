terraform {
  backend "s3" {
    bucket = "alexuaupyconhk24-terraform"
    key    = "state/terraform.tfstate"
    region = "ap-east-1"
  }
}