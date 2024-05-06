resource "aws_vpc" "new_vpc" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support = true
  enable_dns_hostnames = true
  tags = {
    Name = "NewVPC"
  }
}

resource "aws_subnet" "new_subnet" {
  vpc_id            = aws_vpc.new_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "NewSubnet"
  }
}

resource "aws_security_group" "new_sg" {
  name        = "new_security_group"
  description = "Security group for new VPC"
  vpc_id      = aws_vpc.new_vpc.id

  tags = {
    Name = "NewSG"
  }
}

resource "aws_instance" "app_server" {
  ami                   = "ami-04e5276ebb8451442"
  instance_type         = "t2.micro"
  subnet_id             = aws_subnet.new_subnet.id
  vpc_security_group_ids = [aws_security_group.new_sg.id]

  tags = {
    Name = "DemoServerInstance"
  }

  depends_on = [
    aws_vpc.new_vpc,
    aws_subnet.new_subnet,
    aws_security_group.new_sg
  ]
}