import os
import json
import pandas as pd

# Định nghĩa đường dẫn thư mục
RAW_DIR = "data/raw"
CLEANED_DIR = "data/cleaned"

# Tạo thư mục cleaned nếu chưa có
os.makedirs(CLEANED_DIR, exist_ok=True)

def convert_json_to_csv():
    """
    Đọc tất cả file .json trong thư mục /data/raw,
    chuyển đổi sang .csv và lưu vào /data/cleaned
    """
    for filename in os.listdir(RAW_DIR):
        if filename.endswith(".json"):
            json_path = os.path.join(RAW_DIR, filename)
            csv_path = os.path.join(CLEANED_DIR, filename.replace(".json", ".csv"))
            
            try:
                # Đọc dữ liệu JSON
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Nếu JSON là dict có key 'result' (như từ Etherscan API), lấy dữ liệu đó
                if isinstance(data, dict) and "result" in data:
                    data = data["result"]

                # Chuyển sang DataFrame
                df = pd.DataFrame(data)
                
                # Ghi ra file CSV
                df.to_csv(csv_path, index=False, encoding="utf-8")
                print(f"✅ Đã chuyển {filename} → {csv_path}")
            
            except Exception as e:
                print(f"⚠️ Lỗi khi xử lý {filename}: {e}")

if __name__ == "__main__":
    convert_json_to_csv()
