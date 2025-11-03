import os
import json
import psycopg2
from psycopg2 import sql

# ====== CẤU HÌNH DATABASE ======
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "blockchain_dtb",
    "user": "postgres",     
    "password": "123"  
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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                hash TEXT PRIMARY KEY,
                from_address TEXT,
                to_address TEXT,
                value_ether NUMERIC,
                timestamp TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                address TEXT PRIMARY KEY
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS gas_info (
                hash TEXT PRIMARY KEY,
                gas BIGINT,
                gas_used BIGINT,
                gasprice_gwei NUMERIC,
                FOREIGN KEY (hash) REFERENCES transactions(hash)
            );
        """)

        print(" Đã tạo (hoặc tồn tại) 3 bảng: transactions, addresses, gas_info")


# ====== NẠP FILE JSON ======
def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ====== CHÈN DỮ LIỆU ======
def insert_data(conn):
    with conn.cursor() as cur:
        file_types = ["transactions_", "addresses_", "gas_info_"]  # thứ tự nạp
        for prefix in file_types:
            for filename in sorted(os.listdir(SPLIT_DIR)):
                if filename.startswith(prefix):
                    filepath = os.path.join(SPLIT_DIR, filename)
                    data = load_json(filepath)

                    if prefix == "transactions_":
                        for tx in data:
                            cur.execute("""
                                INSERT INTO transactions (hash, from_address, to_address, value_ether, timestamp)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (hash) DO NOTHING;
                            """, (
                                tx.get("hash"),
                                tx.get("from"),
                                tx.get("to"),
                                tx.get("value_Ether"),
                                tx.get("timeStamp")
                            ))
                        print(f" Đã nạp {len(data)} bản ghi vào bảng transactions")

                    elif prefix == "addresses_":
                        for addr in data:
                            cur.execute("""
                                INSERT INTO addresses (address)
                                VALUES (%s)
                                ON CONFLICT (address) DO NOTHING;
                            """, (addr,))
                        print(f" Đã nạp {len(data)} bản ghi vào bảng addresses")

                    elif prefix == "gas_info_":
                        for gas in data:
                            # chỉ chèn nếu hash tồn tại trong transactions
                            cur.execute("SELECT 1 FROM transactions WHERE hash = %s", (gas.get("hash"),))
                            if cur.fetchone():
                                cur.execute("""
                                    INSERT INTO gas_info (hash, gas, gas_used, gasprice_gwei)
                                    VALUES (%s, %s, %s, %s)
                                    ON CONFLICT (hash) DO NOTHING;
                                """, (
                                    gas.get("hash"),
                                    gas.get("gas"),
                                    gas.get("gasUsed"),
                                    gas.get("gasPrice_Gwei")
                                ))
                        print(f" Đã nạp {len(data)} bản ghi vào bảng gas_info (bỏ qua hash chưa có)")


# ====== MAIN ======
if __name__ == "__main__":
    try:
        conn = connect_db()
        create_tables(conn)
        insert_data(conn)
        conn.close()
        print(" Đã hoàn thành quá trình load dữ liệu!")
    except Exception as e:
        print(f" Lỗi trong load.py: {e}")
