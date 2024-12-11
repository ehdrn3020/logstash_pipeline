#!/bin/bash
sudo yum update -y &&
sudo timedatectl set-timezone Asia/Seoul &&
sudo amazon-linux-extras install -y ansible2
