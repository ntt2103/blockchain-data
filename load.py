import os
import json
import psycopg2
import glob
from psycopg2 import sql

# ====== CẤU HÌNH DATABASE ======
DB_CONFIG = {
    "host": "host.docker.internal",
    "port": 5432,
    "database": "blockchain_data",
    "user": "postgres",     
    "password": "password"  
}

# ====== ĐƯỜNG DẪN DỮ LIỆU ======
BASE_DIR = os.path.dirname(__file__)
SPLIT_DIR = os.path.join(BASE_DIR, "data", "cleaned", "split")

# ====== KẾT NỐI DATABASE ======
def connect_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    print(" Kết nối database thành công!")
    return conn


# ====== TẠO BẢNG ======
def create_tables(conn):
    with conn.cursor() as cur:
        # 1. Bảng addresses 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                address TEXT PRIMARY KEY
            );
        """)
        
        # 2. Bảng transactions 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                hash TEXT PRIMARY KEY,
                from_address TEXT,
                to_address TEXT,
                value_ether NUMERIC,
                timestamp TIMESTAMP,
                block_number BIGINT,    -- MỚI
                txreceipt_status TEXT , -- MỚI
                FOREIGN KEY (from_address) REFERENCES addresses(address),
                FOREIGN KEY (to_address) REFERENCES addresses(address)
            );
        """)

        

        # 3. Bảng gas_info 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gas_info (
                hash TEXT PRIMARY KEY,
                gas BIGINT,
                gas_used BIGINT,
                gasprice_gwei NUMERIC,
                FOREIGN KEY (hash) REFERENCES transactions(hash)
            );
        """)
        
        # 4. Bảng contracts 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                hash TEXT PRIMARY KEY,
                contract_address TEXT,
                FOREIGN KEY (hash) REFERENCES transactions(hash)
            );
        """)

        # 5. Bảng function_calls 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS function_calls (
                hash TEXT PRIMARY KEY,
                function_name TEXT,
                method_id TEXT,
                FOREIGN KEY (hash) REFERENCES transactions(hash)
            );
        """)

    print("✅ Đã tạo (hoặc tồn tại) 5 bảng: transactions, addresses, gas_info, contracts, function_calls")


# ====== NẠP FILE JSON (không đổi) ======
def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ====== CHÈN DỮ LIỆU ======
def insert_data(conn):
    with conn.cursor() as cur:
        
        file_types = ["addresses_", "transactions_", "gas_info_", "contracts_", "function_calls_"] 
        
        for prefix in file_types:
            # Tìm file mới nhất cho mỗi prefix
            files_to_load = [f for f in os.listdir(SPLIT_DIR) if f.startswith(prefix)]
            if not files_to_load:
                continue

            # Sắp xếp để lấy file mới nhất (nếu có nhiều file)
            latest_file = sorted(files_to_load)[-1] 
            filepath = os.path.join(SPLIT_DIR, latest_file)
            data = load_json(filepath)

            if not data: # Bỏ qua file rỗng
                continue

            if prefix == "transactions_":
                for tx in data:
                    cur.execute("""
                        INSERT INTO transactions (hash, from_address, to_address, value_ether, timestamp, block_number, txreceipt_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (hash) DO NOTHING;
                    """, (
                        tx.get("hash"),
                        tx.get("from"),
                        tx.get("to"),
                        tx.get("value_Ether"),
                        tx.get("timeStamp"),
                        tx.get("blockNumber"),   # <-- MỚI
                        tx.get("txreceipt_status") # <-- MỚI
                    ))
                print(f"🔵 Đã nạp {len(data)} bản ghi vào bảng transactions")

            elif prefix == "addresses_":
                for addr in data:
                    cur.execute("""
                        INSERT INTO addresses (address) VALUES (%s)
                        ON CONFLICT (address) DO NOTHING;
                    """, (addr,))
                print(f"🔵 Đã nạp {len(data)} bản ghi vào bảng addresses")

            elif prefix == "gas_info_":
                for gas in data:
                    cur.execute("SELECT 1 FROM transactions WHERE hash = %s", (gas.get("hash"),))
                    if cur.fetchone():
                        cur.execute("""
                            INSERT INTO gas_info (hash, gas, gas_used, gasprice_gwei)
                            VALUES (%s, %s, %s, %s) ON CONFLICT (hash) DO NOTHING;
                        """, (
                            gas.get("hash"), gas.get("gas"), gas.get("gasUsed"), gas.get("gasPrice_Gwei")
                        ))
                print(f"🔵 Đã nạp {len(data)} bản ghi vào bảng gas_info")

            # Block chèn cho 'contracts' (MỚI)
            elif prefix == "contracts_":
                for contract in data:
                    cur.execute("SELECT 1 FROM transactions WHERE hash = %s", (contract.get("hash"),))
                    if cur.fetchone():
                        cur.execute("""
                            INSERT INTO contracts (hash, contract_address)
                            VALUES (%s, %s) ON CONFLICT (hash) DO NOTHING;
                        """, (
                            contract.get("hash"), contract.get("contract_address")
                        ))
                print(f"🔵 Đã nạp {len(data)} bản ghi vào bảng contracts")

            # Block chèn cho 'function_calls' (MỚI)
            elif prefix == "function_calls_":
                for func in data:
                    cur.execute("SELECT 1 FROM transactions WHERE hash = %s", (func.get("hash"),))
                    if cur.fetchone():
                        cur.execute("""
                            INSERT INTO function_calls (hash, function_name, method_id)
                            VALUES (%s, %s, %s) ON CONFLICT (hash) DO NOTHING;
                        """, (
                            func.get("hash"), func.get("function_name"), func.get("method_id")
                        ))
                print(f"🔵 Đã nạp {len(data)} bản ghi vào bảng function_calls")

# ====== DỌN DẸP FILE (HÀM MỚI) ======
def cleanup_files():
    """
    Xóa tất cả các file .json trong thư mục raw và split
    """
    # Lấy đường dẫn từ file load.py
    BASE_DIR = os.path.dirname(__file__)
    RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
    SPLIT_DIR = os.path.join(BASE_DIR, "data", "cleaned", "split")

    print("⏳ Bắt đầu dọn dẹp file...")

    # Tìm và xóa file trong data/raw/
    raw_files = glob.glob(os.path.join(RAW_DIR, "*.json"))
    for f in raw_files:
        try:
            os.remove(f)
        except Exception as e:
            print(f"  [Lỗi] Không thể xóa {f}: {e}")
    
    # Tìm và xóa file trong data/cleaned/split/
    split_files = glob.glob(os.path.join(SPLIT_DIR, "*.json"))
    for f in split_files:
        try:
            os.remove(f)
        except Exception as e:
            print(f"  [Lỗi] Không thể xóa {f}: {e}")

    print("✅ Đã dọn dẹp file trong raw/ và split/")
    
# ====== MAIN ======
if __name__ == "__main__":
    try:
        conn = connect_db()
        create_tables(conn)
        insert_data(conn)
        conn.close()
        print(" Đã hoàn thành quá trình load dữ liệu!")
        cleanup_files()
    except Exception as e:
        print(f" Lỗi trong load.py: {e}")