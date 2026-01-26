"""
マーケットデータ取得モジュール

リアルタイムの為替レート、国債利回り等を取得
"""
import yfinance as yf
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class MarketQuote:
    """マーケットクォート"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    previous_close: float
    timestamp: datetime
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "change": self.change,
            "change_percent": self.change_percent,
            "previous_close": self.previous_close,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "direction": "up" if self.change > 0 else ("down" if self.change < 0 else "flat"),
        }


class MarketDataFetcher:
    """マーケットデータ取得クラス"""
    
    # 監視対象シンボル
    SYMBOLS = {
        # 為替
        "USDJPY=X": {"name": "ドル円", "category": "fx"},
        "EURJPY=X": {"name": "ユーロ円", "category": "fx"},
        # 米国債
        "^IRX": {"name": "米国債3ヶ月利回り", "category": "bond"},
        "^FVX": {"name": "米国債5年利回り", "category": "bond"},
        "^TNX": {"name": "米国債10年利回り", "category": "bond"},
        "^TYX": {"name": "米国債30年利回り", "category": "bond"},
        # リスク指標
        "^VIX": {"name": "VIX指数（恐怖指数）", "category": "risk", 
                 "description": "市場のボラティリティ期待。20以下で落ち着き、30超えで警戒"},
        "GC=F": {"name": "ゴールド", "category": "commodity",
                 "description": "安全資産。不安時に買われやすい"},
        "CL=F": {"name": "原油WTI", "category": "commodity",
                 "description": "景気・地政学リスクの指標"},
        # 株式指数
        "^GSPC": {"name": "S&P500", "category": "index",
                  "description": "米国株式市場の代表指数"},
        "^N225": {"name": "日経平均", "category": "index",
                  "description": "日本株式市場の代表指数"},
        "BTC-USD": {"name": "ビットコイン", "category": "crypto",
                    "description": "仮想通貨。リスク選好の指標"},
    }
    
    def fetch_quote(self, symbol: str) -> Optional[MarketQuote]:
        """単一シンボルのクォートを取得"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            
            price = info.get("lastPrice", 0) or info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose", 0) or info.get("regularMarketPreviousClose", 0)
            
            if price == 0:
                # fast_infoで取得できない場合はhistoryから
                hist = ticker.history(period="2d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]
                    prev_close = hist["Close"].iloc[-2] if len(hist) >= 2 else price
            
            change = price - prev_close
            change_percent = (change / prev_close * 100) if prev_close != 0 else 0
            
            symbol_info = self.SYMBOLS.get(symbol, {"name": symbol})
            
            return MarketQuote(
                symbol=symbol,
                name=symbol_info.get("name", symbol),
                price=round(price, 4),
                change=round(change, 4),
                change_percent=round(change_percent, 2),
                previous_close=round(prev_close, 4),
                timestamp=datetime.now(),
            )
        except Exception as e:
            print(f"[MarketData] Error fetching {symbol}: {e}")
            return None
    
    def fetch_all(self) -> Dict[str, Any]:
        """全シンボルのデータを取得"""
        result = {
            "fx": [],
            "bonds": [],
            "risk": [],
            "commodity": [],
            "index": [],
            "crypto": [],
            "timestamp": datetime.now().isoformat(),
        }
        
        for symbol, info in self.SYMBOLS.items():
            quote = self.fetch_quote(symbol)
            if quote:
                category = info.get("category", "other")
                if category in result:
                    result[category].append(quote.to_dict())
        
        return result
    
    def fetch_history(self, symbol: str, period: str = "1mo") -> list:
        """日足ヒストリカルデータを取得"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return []
            
            # Chart.js用のデータ形式に変換
            data = []
            for date, row in hist.iterrows():
                data.append({
                    "date": date.strftime("%m/%d"),
                    "close": round(row["Close"], 4),
                })
            return data
        except Exception as e:
            print(f"[MarketData] Error fetching history for {symbol}: {e}")
            return []
    
    def _calc_weekly_change(self, history: list) -> tuple:
        """週間変動を計算（5営業日前との比較）"""
        if len(history) < 5:
            return 0, 0
        current = history[-1]["close"]
        week_ago = history[-5]["close"] if len(history) >= 5 else history[0]["close"]
        change = current - week_ago
        change_pct = (change / week_ago * 100) if week_ago != 0 else 0
        return round(change, 4), round(change_pct, 2)
    
    def fetch_all_with_history(self) -> Dict[str, Any]:
        """全シンボルのデータ + ヒストリカルデータを取得"""
        result = {
            "fx": [],
            "bonds": [],
            "risk": [],
            "commodity": [],
            "index": [],
            "crypto": [],
            "timestamp": datetime.now().isoformat(),
        }
        
        for symbol, info in self.SYMBOLS.items():
            quote = self.fetch_quote(symbol)
            history = self.fetch_history(symbol, period="1mo")
            
            if quote:
                quote_dict = quote.to_dict()
                quote_dict["history"] = history
                quote_dict["description"] = info.get("description", "")
                
                # 週間変動
                weekly_change, weekly_change_pct = self._calc_weekly_change(history)
                quote_dict["weekly_change"] = weekly_change
                quote_dict["weekly_change_percent"] = weekly_change_pct
                
                category = info.get("category", "other")
                if category in result:
                    result[category].append(quote_dict)
        
        # 日米金利差（10年）を計算
        us10y = next((b for b in result["bonds"] if b["symbol"] == "^TNX"), None)
        # 日本国債10年はyfinanceでは取得困難なので、概算0.8%として計算
        jp10y_rate = 0.8
        if us10y:
            result["interest_rate_diff"] = {
                "us10y": us10y["price"],
                "jp10y": jp10y_rate,
                "diff": round(us10y["price"] - jp10y_rate, 2),
            }
        
        # 逆イールド（2-10年スプレッド）
        us10y_val = us10y["price"] if us10y else None
        us5y = next((b for b in result["bonds"] if b["symbol"] == "^FVX"), None)
        if us10y_val and us5y:
            result["yield_spread"] = {
                "spread_5_10": round(us10y_val - us5y["price"], 2),
            }
        
        return result
    
    def fetch_usdjpy(self) -> Optional[MarketQuote]:
        """ドル円のみ取得"""
        return self.fetch_quote("USDJPY=X")
    
    def fetch_us_bonds(self) -> Dict[str, Optional[MarketQuote]]:
        """米国債利回りを取得"""
        return {
            "10y": self.fetch_quote("^TNX"),
            "30y": self.fetch_quote("^TYX"),
            "5y": self.fetch_quote("^FVX"),
            "3m": self.fetch_quote("^IRX"),
        }


def get_market_data(include_history: bool = True) -> Dict[str, Any]:
    """マーケットデータ取得（簡易関数）"""
    fetcher = MarketDataFetcher()
    if include_history:
        return fetcher.fetch_all_with_history()
    return fetcher.fetch_all()


if __name__ == "__main__":
    # テスト実行
    data = get_market_data()
    print("=== FX ===")
    for fx in data["fx"]:
        print(f"{fx['name']}: {fx['price']} ({fx['change']:+.2f}, {fx['change_percent']:+.2f}%)")
    
    print("\n=== Bonds ===")
    for bond in data["bonds"]:
        print(f"{bond['name']}: {bond['price']}% ({bond['change']:+.3f})")
