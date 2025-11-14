import os
import json
import pandas as pd
# ====== ĐƯỜNG DẪN THƯ MỤC ======
BASE_DIR = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEANED_DIR = os.path.join(BASE_DIR, "data", "cleaned")

# ====== TẠO THƯ MỤC ĐÍCH ======
os.makedirs(CLEANED_DIR, exist_ok=True)


def convert_json_to_csv():
    """
    Đọc toàn bộ file .json trong /data/raw,
    chuyển sang .csv trong /data/cleaned
    """
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".json")]
    if not files:
        print("⚠️ Không có file JSON nào trong thư mục /data/raw")
        return

    for filename in files:
        json_path = os.path.join(RAW_DIR, filename)
        csv_path = os.path.join(CLEANED_DIR, filename.replace(".json", ".csv"))

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Nếu dữ liệu là dict có key "result" (từ Etherscan API)
            if isinstance(data, dict) and "result" in data:
                data = data["result"]

            # Nếu dữ liệu không hợp lệ hoặc rỗng
            if not isinstance(data, list) or len(data) == 0:
                print(f"⚠️ Bỏ qua {filename} (không có dữ liệu hợp lệ)")
                continue

            # Chuyển sang DataFrame và lưu CSV
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False, encoding="utf-8")

            print(f"✅ Đã chuyển {filename} → {csv_path} ({len(df)} dòng)")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý {filename}: {e}")


if __name__ == "__main__":
    convert_json_to_csv()
