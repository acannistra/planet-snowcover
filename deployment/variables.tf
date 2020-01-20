# @@@@@@@@@@ Important Variables
variable "aws_profile" {
  default = "esip"
}
variable "public_key" {
  description = "Public key path"
  default = "~/.ssh/esip-cannistra.pub"
}
variable "private_key" {
  default = "~/.ssh/esip-cannistra.pem"
}

# You can leave these alone.
variable "region" {
  default = "us-west-2"
}
variable "availability_zone" {
  description = "availability zone to create subnet"
  default = "us-west-2a"
}
variable "instance_type" {
  description = "type for aws EC2 instance"
  default = "t3.medium"
}
variable "cidr_vpc" {
  description = "CIDR block for the VPC"
  default = "10.1.0.0/16"
}
variable "cidr_subnet" {
  description = "CIDR block for the subnet"
  default = "10.1.0.0/24"
}
variable "instance_ami" {
  description = "AMI for aws EC2 instance"
  default = "ami-001083bce630cc561"
}

variable "environment_tag" {
  description = "Environment tag"
  default = "Production"
}
