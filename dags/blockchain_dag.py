import os
from datetime import datetime
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
import pendulum

# -----------------------------------------------------------------
# ĐÂY LÀ ĐƯỜNG DẪN BÊN TRONG DOCKER
# (Chúng ta đã định nghĩa nó ở Bước 3 trong docker-compose.yaml)
PROJECT_PATH_IN_DOCKER = "/opt/airflow/scripts"
# -----------------------------------------------------------------
RAW_DATA_PATH = os.path.join(PROJECT_PATH_IN_DOCKER, "data", "raw", "*.json")
SPLIT_DATA_PATH = os.path.join(PROJECT_PATH_IN_DOCKER, "data", "cleaned", "split", "*.json")

# Định nghĩa các lệnh bash
# Lệnh 'cd' rất quan trọng để đảm bảo các script
# tìm thấy file .env và tạo thư mục 'data' đúng chỗ
cmd_extract = f"cd {PROJECT_PATH_IN_DOCKER} && python extract.py"
cmd_transform = f"cd {PROJECT_PATH_IN_DOCKER} && python transform.py"
cmd_load = f"cd {PROJECT_PATH_IN_DOCKER} && python load.py"

# Lệnh dọn dẹp MỚI
cmd_cleanup = f"rm -f {RAW_DATA_PATH} && rm -f {SPLIT_DATA_PATH}"

local_tz = pendulum.timezone("Asia/Ho_Chi_Minh")

with DAG(
    dag_id="etherscan_docker_etl_pipeline",
    description="Pipeline ETL Etherscan chạy trên Docker.",
    start_date=datetime(2025, 11, 8, 0, 0, tzinfo=local_tz),
    schedule="0 */2 * * *",
    catchup=False,
    tags=["crypto", "etl", "docker"],
) as dag:

    # Task 1: Extract
    task_extract = BashOperator(
        task_id="extract_data",
        bash_command=cmd_extract,
        doc_md="Chạy script extract.py để tải dữ liệu thô.",
    )

    # Task 2: Transform
    task_transform = BashOperator(
        task_id="transform_data",
        bash_command=cmd_transform,
        doc_md="Chạy script transform.py để làm sạch dữ liệu.",
    )

    # Task 3: Load
    task_load = BashOperator(
        task_id="load_data",
        bash_command=cmd_load,
        doc_md="Chạy script load.py để nạp dữ liệu vào Postgres.",
    )
    # task 4: clear
    task_cleanup = BashOperator(
        task_id="cleanup_processed_files",
        bash_command=cmd_cleanup,
    )

    # Định nghĩa thứ tự chạy
    task_extract >> task_transform >> task_load >> task_cleanup