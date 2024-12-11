import os
import random
from datetime import datetime
import time

def generate_data(data_dir):
    while True:
        item_id = random.choice(["A", "B", "C"])
        created_at = datetime.now().isoformat()
        date_str = datetime.now().strftime("%Y%m%d")
        file_path = f"{data_dir}/{item_id}/{date_str}.dat"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "a") as file:
            file.write(f"{item_id},{created_at}\n")
            print("file create")

        time.sleep(0.1)  # 초당 10건을 생성하기 위해 0.1초마다 실행

generate_data('/home/ec2-user/logs') # 파일 저장 경로