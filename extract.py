import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Nạp biến môi trường
load_dotenv()

API_KEY = os.getenv("ETHERSCAN_API_KEY")
if not API_KEY:
    raise ValueError("❌ Không tìm thấy ETHERSCAN_API_KEY trong file .env")

# API endpoint (có thể chỉnh cho testnet hoặc chain khác)
BASE_URL = os.getenv("ETHERSCAN_BASE_URL", "https://api.etherscan.io/v2/api")

# Đảm bảo thư mục lưu dữ liệu tồn tại
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(DATA_DIR, exist_ok=True)


def get_transactions(address, start_block=0, end_block=99999999, sort="desc", chainid=None):
    """
    Lấy danh sách giao dịch của một địa chỉ Ethereum từ Etherscan API (v2).
    """
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": start_block,
        "endblock": end_block,
        "sort": sort,
        "apikey": API_KEY
    }

    if chainid:
        params["chainid"] = str(chainid)

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    # Kiểm tra phản hồi hợp lệ
    if isinstance(data, dict) and data.get("status") == "0":
        raise Exception(f"Lỗi từ Etherscan API: {data.get('message')}")

    return data.get("result", data)


def save_raw_data(address, data):
    """
    Lưu dữ liệu thô ra file JSON trong thư mục /data/raw
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_addr = address[:6]  # chỉ lấy vài ký tự đầu cho gọn
    filename = f"{short_addr}_transactions_{timestamp}.json"
    filepath = os.path.join(DATA_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✅ Đã lưu dữ liệu vào: {filepath}")


if __name__ == "__main__":
    # Ví dụ địa chỉ ví (bạn có thể thay)
    example_address = "0xdac17f958d2ee523a2206206994597c13d831ec7"

    try:
        print("⏳ Đang tải dữ liệu từ Etherscan...")
        transactions = get_transactions(example_address, chainid=1)
        save_raw_data(example_address, transactions)
    except Exception as e:
        print(f"❌ Lỗi: {e}")