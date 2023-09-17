#output "instance_ip_addr" {
#  value = aws_instance.web.*.public_ip
#}

output "ono_server_instance_ip_addr" {
  value = aws_instance.ono_server.*.public_ip
}
