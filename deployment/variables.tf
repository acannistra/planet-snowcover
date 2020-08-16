# @@@@@@@@@@ Important Variables
variable "aws_profile" {
  default = "esip_deploy"
}

variable "public_key" {
  description = "Public key path"
  default     = "~/.ssh/snowmap.pub"
}

variable "private_key" {
  default = "~/.ssh/snowmap"
}

# You can leave these alone.
variable "region" {
  default = "us-west-2"
}

variable "availability_zone" {
  description = "availability zone to create subnet"
  default     = "us-west-2a"
}

variable "instance_type" {
  description = "type for aws EC2 instance"
  default     = "t3.medium"
}

variable "cidr_vpc" {
  description = "CIDR block for the VPC"
  default     = "10.1.0.0/16"
}

variable "cidr_subnet" {
  description = "CIDR block for the subnet"
  default     = "10.1.0.0/24"
}

variable "instance_ami" {
  description = "AMI for aws EC2 instance"
  default     = "ami-001083bce630cc561"
}

variable "ec2_default_policy_arn" {
  description = "default policy to attach to EC2 role (via ARN)."
  default     = "arn:aws:iam::aws:policy/PowerUserAccess"
}

variable "environment_tag" {
  description = "Environment tag"
  default     = "Production"
}

variable "DOCKERHUB_IMAGE" {
  description = "Dockerhub location of main toolset image for dev + sage."
  default     = "tonycannistra/planet-snowcover:latest"
}
