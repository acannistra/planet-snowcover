#providers
provider "aws" {
  region                  = var.region
  shared_credentials_file = "~/.aws/credentials"
  profile                 = var.aws_profile
}

#resources

## ECR
resource "aws_ecr_repository" "ps_ecr" {
  name                 = "ps-images"
  image_tag_mutability = "MUTABLE"
}

## EC2
resource "aws_vpc" "vpc" {
  cidr_block           = var.cidr_vpc
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Environment = var.environment_tag
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id
  tags = {
    Environment = var.environment_tag
  }
}

resource "aws_subnet" "subnet_public" {
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = var.cidr_subnet
  map_public_ip_on_launch = "true"
  availability_zone       = var.availability_zone
  tags = {
    Environment = var.environment_tag
  }
}

resource "aws_route_table" "rtb_public" {
  vpc_id = aws_vpc.vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Environment = var.environment_tag
  }
}

resource "aws_route_table_association" "rta_subnet_public" {
  subnet_id      = aws_subnet.subnet_public.id
  route_table_id = aws_route_table.rtb_public.id
}

resource "aws_security_group" "sg_22_80" {
  name   = "sg_22"
  vpc_id = aws_vpc.vpc.id

  # SSH access from the VPC
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port = 8888
    to_port = 8888
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment_tag
  }
}

resource "aws_key_pair" "ec2key" {
  key_name   = "publicKey"
  public_key = file(var.public_key)
}

## Create acess role for EC2 instance.
resource "aws_iam_role" "EC2_access_role" {
  name = "EC2_access_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

}

# Attach policy to above role.
resource "aws_iam_role_policy_attachment" "ec2_enable" {
  role       = aws_iam_role.EC2_access_role.name
  policy_arn = var.ec2_default_policy_arn
}

# Create instance profile for EC2 instance w/ above  role
resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "main_ec2_profile"
  role = aws_iam_role.EC2_access_role.name
}

# create instance
resource "aws_instance" "mainDevInstance" {
  ami                    = var.instance_ami
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.subnet_public.id
  vpc_security_group_ids = [aws_security_group.sg_22_80.id]
  key_name               = aws_key_pair.ec2key.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_instance_profile.name

  tags = {
    Environment = var.environment_tag
  }

  provisioner "file" {
    source      = "~/.aws/"
    destination = "/home/ubuntu/"
  }

  # uploads docker image in DockerHub to newly-created ECR
  provisioner "remote-exec" {
    inline = [
      "sudo docker pull ${var.DOCKERHUB_IMAGE}",
      "sudo docker tag ${var.DOCKERHUB_IMAGE} ${aws_ecr_repository.ps_ecr.repository_url}:latest",
      "sudo $(aws ecr get-login --no-include-email)",
      "sudo docker push ${aws_ecr_repository.ps_ecr.repository_url}:latest",
    ]
  }

  connection {
    type        = "ssh"
    user        = "ubuntu"
    host        = self.public_dns
    private_key = file(var.private_key)
  }
}

## Sagemaker

resource "aws_iam_role" "sagemaker_role" {
  name = "sagemaker-role"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "sagemaker.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }
EOF

}

resource "aws_iam_policy" "s3-access-policy" {
  name        = "sagemaker-s3-access-policy"
  description = "So Sagemaker roles can access S3."

  policy = <<EOF
{
  	"Version": "2012-10-17",
  	"Statement": [{
  		"Effect": "Allow",
  		"Action": [
  			"s3:GetObject",
  			"s3:PutObject",
  			"s3:DeleteObject",
  			"s3:ListBucket"
  		],
  		"Resource": [
  			"arn:aws:s3:::*"
  		]
  	}]
}
EOF

}

resource "aws_iam_role_policy_attachment" "attach-sage-fullaccess" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "attach-sage-s3access" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = aws_iam_policy.s3-access-policy.arn
}
