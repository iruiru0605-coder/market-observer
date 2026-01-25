"""Google News RSS 接続テスト"""
import requests
import time

print("Google News RSS 接続テスト")
print("=" * 40)

url = "https://news.google.com/rss/search?q=forex&hl=en-US&gl=US&ceid=US:en"

try:
    start = time.time()
    response = requests.get(url, timeout=15, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    elapsed = time.time() - start
    
    print(f"ステータス: {response.status_code}")
    print(f"応答時間: {elapsed:.2f}秒")
    print(f"コンテンツ長: {len(response.content)} bytes")
    
    if response.status_code == 200:
        print("\n✅ 接続成功！")
        # 最初の500文字を表示
        print(f"\n内容プレビュー:\n{response.text[:500]}")
    else:
        print(f"\n❌ エラー: {response.status_code}")
        print(response.text[:500])
        
except requests.exceptions.Timeout:
    print("❌ タイムアウト (15秒)")
except requests.exceptions.RequestException as e:
    print(f"❌ リクエストエラー: {e}")
