output "public_instance_ip" {
  value = [aws_instance.mainDevInstance.public_ip]
}

output "SSH_CMD" {
  value = "ssh -i ${var.private_key} ubuntu@${aws_instance.mainDevInstance.public_ip}"
}

output "sagemaker_role_arn" {
  value = aws_iam_role.sagemaker_role.arn
}
