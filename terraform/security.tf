resource "aws_security_group" "opspulse_sg" {
  name        = "opspulse-security-group"
  description = "Allow web traffic to OpsPulse"

  ingress {
    description = "HTTP"
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
    Name = "OpsPulse-Security-Group"
  }
}

