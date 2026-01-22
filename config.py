"""
Market Observer - 設定ファイル
"""
import os
from pathlib import Path
from datetime import datetime

# .envファイルから環境変数を読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# パス設定
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"

# ログディレクトリ作成
LOG_DIR.mkdir(parents=True, exist_ok=True)

# API設定
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# スコア設定
SCORE_MIN = -10
SCORE_MAX = 10

# アラート閾値
ALERT_DAILY_CHANGE = 3      # 前日比 ±3 以上で警告
ALERT_MA_WINDOW = 3         # 移動平均ウィンドウ
ALERT_DOMESTIC_FOREIGN_GAP = 5  # 国内外スコア差

# 分類カテゴリ
CATEGORIES = {
    "market": "市場全体",
    "sector": "セクター",
    "theme": "テーマ",
}

# ログファイル名
def get_log_filename():
    return LOG_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
