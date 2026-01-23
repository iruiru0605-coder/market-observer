"""
履歴管理モジュール
過去のレポートデータを集計・比較

【重要】
- 過去データは「比較のための参考情報」として扱う
- 将来予測や売買示唆には使用しない
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import LOG_DIR


class HistoryManager:
    """履歴管理クラス"""
    
    HISTORY_FILE = LOG_DIR / "history.json"
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self._load()
    
    def _load(self) -> None:
        """履歴ファイルを読み込み"""
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = []
    
    def _save(self) -> None:
        """履歴ファイルを保存"""
        with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def add_daily_record(
        self,
        total_score: float,
        zero_ratio: float,
        plus2_ratio: float,
        minus2_ratio: float,
        news_count: int,
        macro_ratio: float = 0
    ) -> None:
        """日次記録を追加"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 同日の記録があれば更新
        for record in self.history:
            if record.get("date") == today:
                record.update({
                    "total_score": total_score,
                    "zero_ratio": zero_ratio,
                    "plus2_ratio": plus2_ratio,
                    "minus2_ratio": minus2_ratio,
                    "news_count": news_count,
                    "macro_ratio": macro_ratio,
                })
                self._save()
                return
        
        # 新規追加
        self.history.append({
            "date": today,
            "total_score": total_score,
            "zero_ratio": zero_ratio,
            "plus2_ratio": plus2_ratio,
            "minus2_ratio": minus2_ratio,
            "news_count": news_count,
            "macro_ratio": macro_ratio,
        })
        
        # 30日以上古いデータは削除
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        self.history = [r for r in self.history if r.get("date", "") >= cutoff]
        
        self._save()
    
    def get_last_n_days(self, n: int = 7) -> List[Dict[str, Any]]:
        """過去n日分のデータを取得"""
        today = datetime.now().strftime("%Y-%m-%d")
        cutoff = (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")
        
        return [
            r for r in self.history
            if cutoff <= r.get("date", "") < today
        ]
    
    def get_7day_comparison(self, current: Dict[str, Any]) -> Dict[str, Any]:
        """
        過去7日間との比較データを生成
        
        Args:
            current: 当日のデータ {total_score, zero_ratio, plus2_ratio, minus2_ratio}
        
        Returns:
            比較データ
        """
        past_records = self.get_last_n_days(7)
        
        if not past_records:
            return {
                "has_history": False,
                "days_count": 0,
            }
        
        # 平均値を計算
        avg_total = sum(r.get("total_score", 0) for r in past_records) / len(past_records)
        avg_zero = sum(r.get("zero_ratio", 0) for r in past_records) / len(past_records)
        avg_plus2 = sum(r.get("plus2_ratio", 0) for r in past_records) / len(past_records)
        avg_minus2 = sum(r.get("minus2_ratio", 0) for r in past_records) / len(past_records)
        
        return {
            "has_history": True,
            "days_count": len(past_records),
            "avg_total_score": round(avg_total, 2),
            "avg_zero_ratio": round(avg_zero, 1),
            "avg_plus2_ratio": round(avg_plus2, 1),
            "avg_minus2_ratio": round(avg_minus2, 1),
            "current_total_score": current.get("total_score", 0),
            "current_zero_ratio": current.get("zero_ratio", 0),
            "current_plus2_ratio": current.get("plus2_ratio", 0),
            "current_minus2_ratio": current.get("minus2_ratio", 0),
        }
    
    def get_consecutive_high_zero_days(self) -> int:
        """評価保留80%超の連続日数を取得"""
        today = datetime.now().strftime("%Y-%m-%d")
        count = 0
        
        # 最新から遡って確認
        sorted_history = sorted(self.history, key=lambda x: x.get("date", ""), reverse=True)
        
        for record in sorted_history:
            if record.get("date") == today:
                continue  # 当日は除外
            if record.get("zero_ratio", 0) > 80:
                count += 1
            else:
                break
        
        return count


def get_history_manager() -> HistoryManager:
    """履歴マネージャーを取得"""
    return HistoryManager()
