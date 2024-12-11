#!/bin/bash

# EC2 이름
ec2_name=$1

# AWS 인증 정보 설정 ( .env )
if [[ -f setting_aws/.env ]]; then
    source setting_aws/.env
else
    echo "Error: .env 파일을 찾을 수 없습니다."
    exit 1
fi

# 필수 변수 검증
if [[ -z $AWS_ACCESS_KEY_ID || -z $AWS_SECRET_ACCESS_KEY || -z $AWS_DEFAULT_REGION ]]; then
    echo "Error: AWS 환경 변수가 설정되지 않았습니다."
    exit 1
fi

# AWS 인증 정보 설정
export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
export AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION

# 사용자 스크립트 내용을 base64로 인코딩
USER_SCRIPT=$(cat setting_aws/user_script.sh | base64)

# Spot 인스턴스 생성
spot_instance_request_id=$(aws ec2 request-spot-instances \
    --instance-count 1 \
    --type "one-time" \
    --launch-specification "{
        \"ImageId\": \"$AMI_ID\",
        \"InstanceType\": \"$INSTANCE_TYPE\",
        \"SubnetId\": \"$SUBNET_ID\",
        \"SecurityGroupIds\": [\"$SECURITY_GROUP_IDS\"],
        \"KeyName\": \"$KEY_NAME\",
        \"UserData\": \"$USER_SCRIPT\"
    }" \
    --spot-price $SPOT_PRICE \
    --query 'SpotInstanceRequests[0].SpotInstanceRequestId' \
    --output text)

# Spot 인스턴스가 생성될 때까지 대기
aws ec2 wait spot-instance-request-fulfilled --spot-instance-request-ids $spot_instance_request_id

# 생성된 Spot 인스턴스의 ID 가져오기
instance_id=$(aws ec2 describe-spot-instance-requests \
    --spot-instance-request-ids $spot_instance_request_id \
    --query 'SpotInstanceRequests[0].InstanceId' \
    --output text)

if [[ -z $instance_id ]]; then
    echo "Error: Spot 인스턴스 생성 실패."
    exit 1
fi

# 생성된 Spot 인스턴스에 태그 추가
aws ec2 create-tags \
    --resources $instance_id \
    --tags Key=Name,Value=$ec2_name

# 생성된 Spot 인스턴스 확인
aws ec2 describe-spot-instance-requests

### Code Upload, Git Clone으로 대체 가능 ###
# EC2 퍼블릭 IP 가져오기
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $instance_id \
    --query "Reservations[0].Instances[0].PublicIpAddress" \
    --output text \
    --region $AWS_DEFAULT_REGION)

# EC2에 코드 업로드
if [ "$PUBLIC_IP" != "None" ]; then
    echo "Uploading $SOURCE_FILE to $PUBLIC_IP:$DEST_PATH 실행"
    scp -i $KEY_PATH -r $SOURCE_FILE ec2-user@$PUBLIC_IP:$DEST_PATH
    echo "Upload 완료."
else
    echo "Instance $instance_id 에 public IP가 없습니다."
fi
