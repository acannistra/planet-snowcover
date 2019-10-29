#providers
provider "aws" {
  region                  = "${var.region}"
  shared_credentials_file = "~/.aws/creds"
  profile                 = "${var.aws_profile}"
}

#resources
resource "aws_vpc" "vpc" {
  cidr_block = "${var.cidr_vpc}"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Environment = "${var.environment_tag}"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = "${aws_vpc.vpc.id}"
  tags = {
    Environment = "${var.environment_tag}"
  }
}

resource "aws_subnet" "subnet_public" {
  vpc_id = "${aws_vpc.vpc.id}"
  cidr_block = "${var.cidr_subnet}"
  map_public_ip_on_launch = "true"
  availability_zone = "${var.availability_zone}"
  tags = {
    Environment = "${var.environment_tag}"
  }
}

resource "aws_route_table" "rtb_public" {
  vpc_id = "${aws_vpc.vpc.id}"

  route {
      cidr_block = "0.0.0.0/0"
      gateway_id = "${aws_internet_gateway.igw.id}"
  }

  tags = {
    Environment = "${var.environment_tag}"
  }
}

resource "aws_route_table_association" "rta_subnet_public" {
  subnet_id      = "${aws_subnet.subnet_public.id}"
  route_table_id = "${aws_route_table.rtb_public.id}"
}

resource "aws_security_group" "sg_22_80" {
  name = "sg_22"
  vpc_id = "${aws_vpc.vpc.id}"

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

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = "${var.environment_tag}"
  }
}

resource "aws_key_pair" "ec2key" {

  key_name = "publicKey"
  public_key = "${file(var.public_key)}"
}

resource "aws_instance" "testInstance" {
  ami           = "${var.instance_ami}"
  instance_type = "${var.instance_type}"
  subnet_id = "${aws_subnet.subnet_public.id}"
  vpc_security_group_ids = ["${aws_security_group.sg_22_80.id}"]
  key_name = "${aws_key_pair.ec2key.key_name}"

  tags = {
		Environment = "${var.environment_tag}"
	}

	provisioner "file" {
    source      = "~/.aws/"
    destination = "/home/ubuntu/"

  }

  provisioner "remote-exec" {
    inline = [
      "sudo $(aws ecr --profile ${var.aws_profile} get-login --no-include-email)",
			"sudo docker pull 675906086666.dkr.ecr.us-west-2.amazonaws.com/planet-snowcover",
    ]
  }

  connection {
    type     = "ssh"
    user     = "ubuntu"
		host     = "${self.public_dns}"
    private_key = "${file(var.private_key)}"
  }
}

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
  role       = "${aws_iam_role.sagemaker_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "attach-sage-s3access" {
  role       = "${aws_iam_role.sagemaker_role.name}"
  policy_arn = "${aws_iam_policy.s3-access-policy.arn}"
}
