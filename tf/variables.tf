variable "aws_key_pair_name" {
  type    = string
  default = "id_rsa"
}

variable "cidr_block" {
  type    = string
  default = "10.0.0.0/16"
}

variable "subnet" {
  default = "10.0.0.0/24"
}

variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "availability_zone" {
  type    = string
  default = "eu-central-1a"
}

variable "instance_type_main" {
  type    = string
  default = "t2.small"
}