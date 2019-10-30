output "vpc_id" {
  value = "${aws_vpc.vpc.id}"
}
output "public_subnets" {
  value = ["${aws_subnet.subnet_public.id}"]
}
output "public_route_table_ids" {
  value = ["${aws_route_table.rtb_public.id}"]
}
output "public_instance_ip" {
  value = ["${aws_instance.testInstance.public_ip}"]
}
output "SSH_HERE" {
  value = "ssh -i ${var.private_key} ubuntu@${aws_instance.testInstance.public_ip}"
}
output "sagemaker_role_arn"{
  value = "${aws_iam_role.sagemaker_role.arn}"
}
