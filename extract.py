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

# Sử dụng API V2 (theo yêu cầu của Etherscan)
BASE_URL = os.getenv("ETHERSCAN_BASE_URL", "https://api.etherscan.io/v2/api")

# Đảm bảo thư mục lưu dữ liệu tồn tại
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(DATA_DIR, exist_ok=True)


def get_transactions(address, start_block=0, end_block=99999999, sort="desc"):
    """
    Lấy danh sách giao dịch của một địa chỉ Ethereum từ Etherscan API.
    Lưu ý: Không dùng chainid với API v1
    """
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": start_block,
        "endblock": end_block,
        "sort": sort,
        "apikey": API_KEY,
        "chainid": 1  
    }

    print(f"🔍 Đang gọi API: {BASE_URL}")
    print(f"📦 Params: module={params['module']}, action={params['action']}")
    
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    
    # Debug: In ra response để kiểm tra
    print(f"📥 API Response status: {data.get('status')}")
    print(f"📥 API Response message: {data.get('message')}")

    # Kiểm tra phản hồi hợp lệ
    if isinstance(data, dict) and data.get("status") == "0":
        if data.get("message") == "No transactions found":
            print("⚠️  Không tìm thấy giao dịch nào")
            return []
        # In ra lỗi chi tiết
        error_msg = data.get('message', 'Unknown error')
        result = data.get('result', 'No result')
        raise Exception(f"Lỗi từ Etherscan API: {error_msg} | Result: {result}")

    return data.get("result", [])


def save_raw_data(address, data):
    """
    Lưu dữ liệu thô ra file JSON trong thư mục /data/raw
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_addr = address[:6]
    filename = f"{short_addr}_transactions_{timestamp}.json"
    filepath = os.path.join(DATA_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✅ Đã lưu {len(data)} giao dịch vào: {filepath}")
    return filepath


def analyze_addresses_quick(data, wallet_address):
    """
    Phân tích nhanh số lượng địa chỉ unique trong from và to
    """
    from_addrs = set()
    to_addrs = set()
    
    for tx in data:
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "").lower()
        
        if from_addr and from_addr != wallet_address.lower():
            from_addrs.add(from_addr)
        if to_addr and to_addr != wallet_address.lower():
            to_addrs.add(to_addr)
    
    print(f"\n📊 Phân tích dữ liệu:")
    print(f"   ├─ Tổng giao dịch: {len(data)}")
    print(f"   ├─ Unique FROM addresses: {len(from_addrs)}")
    print(f"   ├─ Unique TO addresses: {len(to_addrs)}")
    print(f"   └─ Tổng unique addresses: {len(from_addrs | to_addrs)}")
    
    return {
        "from_count": len(from_addrs),
        "to_count": len(to_addrs),
        "total_unique": len(from_addrs | to_addrs)
    }


if __name__ == "__main__":
    
    WALLETS = {
        "binance": {
            "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
            "name": "Binance Hot Wallet",
            "description": "Exchange wallet - rất nhiều giao dịch đa dạng"
        },
        "vitalik": {
            "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "name": "Vitalik Buterin",
            "description": "Founder Ethereum - giao dịch thú vị"
        },
        "coinbase": {
            "address": "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3",
            "name": "Coinbase",
            "description": "Exchange wallet - volume cao"
        },
        "whale": {
            "address": "0x220866B1A2219f40e72f5c628B65D54268cA3A9D",
            "name": "Unknown Whale",
            "description": "Whale wallet - large transactions"
        }
    }
    
    selected_wallet = "vitalik"  # binance, vitalik, coinbase, hoặc whale
    
    wallet_info = WALLETS[selected_wallet]
    example_address = wallet_info["address"]
    
    print("=" * 70)
    print(f"🎯 Ví được chọn: {wallet_info['name']}")
    print(f"📍 Địa chỉ: {example_address}")
    print(f"📝 Mô tả: {wallet_info['description']}")
    print("=" * 70)

    try:
        print("\n⏳ Đang tải dữ liệu từ Etherscan...")
        
        # Lấy 1000 giao dịch gần nhất (để tránh timeout)
        transactions = get_transactions(
            example_address, 
            sort="desc"
        )
        
        if not transactions:
            print("❌ Không có dữ liệu để lưu")
        else:
            filepath = save_raw_data(example_address, transactions)
            
            # Phân tích nhanh
            stats = analyze_addresses_quick(transactions, example_address)
            
            print(f"\n💡 Gợi ý Power BI:")
            if stats["from_count"] > 10 and stats["to_count"] > 10:
                print("   ✅ Dữ liệu tốt! Có nhiều địa chỉ khác nhau trong cả FROM và TO")
                print("   ✅ Phù hợp để tạo Network Graph và Flow Analysis")
            else:
                print("   ⚠️  Dữ liệu có thể không đủ đa dạng")
                print(f"   💡 Thử ví khác: {', '.join([k for k in WALLETS.keys() if k != selected_wallet])}")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print("\n💡 Gợi ý khắc phục:")
        print("   1. Kiểm tra API key trong file .env")
        print("   2. Kiểm tra BASE_URL (phải là https://api.etherscan.io/api)")
        print("   3. Thử ví khác nếu ví hiện tại không có giao dịch")
