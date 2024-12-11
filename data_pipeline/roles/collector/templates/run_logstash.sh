#!/bin/bash

# Run Logstash
LOG_DATE=$(date "+%Y%m%d") \
/home/ec2-user/packages/logstash-8.16.0/bin/logstash \
-f /home/ec2-user/packages/logstash-8.16.0/config/collector.conf