import os
import json
from datetime import datetime, timezone, timedelta
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

    # === THÊM DÒNG NÀY ===
    # Định nghĩa múi giờ UTC+7 (Giờ Việt Nam)
    local_timezone = timezone(timedelta(hours=7))
    # ====================

    for tx in data:
        if tx.get("isError") == "1":
            continue

        tx_hash = tx.get("hash")
        if not tx_hash or tx_hash in seen_hashes:
            continue

        seen_hashes.add(tx_hash)

        # === THAY ĐỔI KHỐI CODE NÀY ===
        try:
            # 1. Lấy timestamp gốc (là UTC)
            utc_timestamp_int = int(tx["timeStamp"])
            
            # 2. Tạo đối tượng datetime, chỉ định rõ nó là UTC
            utc_dt = datetime.fromtimestamp(utc_timestamp_int, tz=timezone.utc)
            
            # 3. Chuyển đổi nó sang múi giờ địa phương (UTC+7)
            local_dt = utc_dt.astimezone(local_timezone)
            
            # 4. Lưu dưới dạng ISO string (bây giờ sẽ là 22:16:29...)
            tx["timeStamp"] = local_dt.isoformat()
        except Exception:
            tx["timeStamp"] = None
        # === KẾT THÚC THAY ĐỔI ===

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
    cleaned.sort(key=lambda x: x["timeStamp"] or "", reverse=True)
    return cleaned


def split_into_tables(clean_data):
    """
    Chia dữ liệu thành 5 bảng (dạng JSON riêng)
    """
    transactions = []
    addresses = set()
    gas_info = []
    contracts = []       
    function_calls = []  

    for tx in clean_data:
        tx_hash = tx.get("hash")
        
        # 1. Bảng giao dịch chính (Thêm blockNumber và status)
        transactions.append({
            "hash": tx_hash,
            "from": tx.get("from"),
            "to": tx.get("to"),
            "value_Ether": tx.get("value_Ether"),
            "timeStamp": tx.get("timeStamp"),
            "blockNumber": tx.get("blockNumber"),          
            "txreceipt_status": tx.get("txreceipt_status") 
        })

        # 2. Bảng địa chỉ (không đổi)
        if tx.get("from"):
            addresses.add(tx["from"])
        if tx.get("to"):
            addresses.add(tx["to"])

        # 3. Bảng gas (không đổi)
        gas_info.append({
            "hash": tx_hash,
            "gas": tx.get("gas"),
            "gasUsed": tx.get("gasUsed"),
            "gasPrice_Gwei": tx.get("gasPrice_Gwei")
        })

        # 4. Bảng contracts (MỚI)
        # Chỉ thêm nếu 'contractAddress' có giá trị (tức là giao dịch này tạo ra 1 contract)
        contract_addr = tx.get("contractAddress")
        if contract_addr and contract_addr != "": 
            contracts.append({
                "hash": tx_hash,
                "contract_address": contract_addr
            })

        # 5. Bảng function_calls (MỚI)
        # Chỉ thêm nếu 'functionName' có giá trị (tức là 1 tương tác với contract)
        func_name = tx.get("functionName")
        if func_name and func_name != "":
            function_calls.append({
                "hash": tx_hash,
                "function_name": func_name,
                "method_id": tx.get("methodId")
            })

    # Lưu thành 5 file riêng
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Hàm phụ trợ để lưu file
    def save_split_file(data, name, ts):
        if not data: # Không lưu file rỗng
            print(f"⚠️ Bỏ qua file {name} vì không có dữ liệu.")
            return
        filepath = os.path.join(SPLIT_DIR, f"{name}_{ts}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    save_split_file(transactions, "transactions", timestamp)
    save_split_file(sorted(list(addresses)), "addresses", timestamp)
    save_split_file(gas_info, "gas_info", timestamp)
    save_split_file(contracts, "contracts", timestamp)           # <-- LƯU FILE MỚI
    save_split_file(function_calls, "function_calls", timestamp) # <-- LƯU FILE MỚI

    print(f"✅ Đã chia dữ liệu thành 5 bảng: transactions, addresses, gas_info, contracts, function_calls")


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