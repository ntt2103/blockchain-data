import os
import json
from datetime import datetime
from decimal import Decimal

# Đường dẫn thư mục dữ liệu
BASE_DIR = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEANED_DIR = os.path.join(BASE_DIR, "data", "cleaned")
SPLIT_DIR = os.path.join(CLEANED_DIR, "split")
os.makedirs(SPLIT_DIR, exist_ok=True)

def load_raw_files():
    all_data = []
    for filename in os.listdir(RAW_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(RAW_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_data.extend(data)
    print(f" Đã đọc {len(all_data)} giao dịch từ thư mục raw/")
    return all_data

def clean_and_transform(data):
    cleaned = []
    seen_hashes = set()

    for tx in data:
        if tx.get("isError") == "1":
            continue

        tx_hash = tx.get("hash")
        if not tx_hash or tx_hash in seen_hashes:
            continue

        seen_hashes.add(tx_hash)

        try:
            tx["timeStamp"] = datetime.fromtimestamp(int(tx["timeStamp"])).isoformat()
        except Exception:
            tx["timeStamp"] = None

        try:
            tx["value_Ether"] = float(Decimal(tx["value"]) / Decimal(1e18))
        except Exception:
            tx["value_Ether"] = 0.0

        try:
            tx["gasPrice_Gwei"] = float(Decimal(tx["gasPrice"]) / Decimal(1e9))
        except Exception:
            tx["gasPrice_Gwei"] = 0.0

        cleaned.append(tx)

    print(f" Sau khi làm sạch: còn {len(cleaned)} giao dịch hợp lệ.")
    return cleaned


def split_into_tables(clean_data):
    """
    Chia dữ liệu thành nhiều bảng (dạng JSON riêng)
    """
    transactions = []
    addresses = set()
    gas_info = []

    for tx in clean_data:
        # Bảng giao dịch chính
        transactions.append({
            "hash": tx.get("hash"),
            "from": tx.get("from"),
            "to": tx.get("to"),
            "value_Ether": tx.get("value_Ether"),
            "timeStamp": tx.get("timeStamp"),
        })

        # Bảng địa chỉ
        if tx.get("from"):
            addresses.add(tx["from"])
        if tx.get("to"):
            addresses.add(tx["to"])

        # Bảng gas
        gas_info.append({
            "hash": tx.get("hash"),
            "gas": tx.get("gas"),
            "gasUsed": tx.get("gasUsed"),
            "gasPrice_Gwei": tx.get("gasPrice_Gwei")
        })

    # Lưu thành file riêng
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(SPLIT_DIR, f"transactions_{timestamp}.json"), "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=4, ensure_ascii=False)

    with open(os.path.join(SPLIT_DIR, f"addresses_{timestamp}.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(list(addresses)), f, indent=4, ensure_ascii=False)

    with open(os.path.join(SPLIT_DIR, f"gas_info_{timestamp}.json"), "w", encoding="utf-8") as f:
        json.dump(gas_info, f, indent=4, ensure_ascii=False)

    print(f"✅ Đã chia dữ liệu thành 3 bảng: transactions, addresses, gas_info")


def save_clean_data(data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(CLEANED_DIR, f"clean_transactions_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f" Đã lưu dữ liệu sạch vào: {output_path}")


if __name__ == "__main__":
    try:
        raw_data = load_raw_files()
        clean_data = clean_and_transform(raw_data)
        save_clean_data(clean_data)
        split_into_tables(clean_data)
    except Exception as e:
        print(f" Lỗi trong transform.py: {e}")
