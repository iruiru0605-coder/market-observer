"""
アラート検知モジュール
変化点・異常を検出
"""
from typing import Dict, Any, List, Optional
from config import ALERT_DAILY_CHANGE, ALERT_MA_WINDOW, ALERT_DOMESTIC_FOREIGN_GAP


class AlertDetector:
    """アラート検知クラス"""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
    
    def add_daily_score(self, aggregate_scores: Dict[str, Any]) -> None:
        """日次スコアを履歴に追加"""
        self.history.append(aggregate_scores)
    
    def detect_alerts(self, current_scores: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        アラートを検出
        
        検出条件:
        1. 前日比 ±3 以上の変化
        2. 3日移動平均の符号反転
        3. 国内外スコア差 ±5 以上
        """
        alerts = []
        
        # === 1. 前日比変化 ===
        if len(self.history) >= 1:
            prev_score = self.history[-1].get("total_score", 0)
            curr_score = current_scores.get("total_score", 0)
            daily_change = curr_score - prev_score
            
            if abs(daily_change) >= ALERT_DAILY_CHANGE:
                direction = "上昇" if daily_change > 0 else "下落"
                alerts.append({
                    "type": "daily_change",
                    "severity": "warning" if abs(daily_change) >= 5 else "info",
                    "message": f"総合スコアが前日比 {daily_change:+.1f} 変化（{direction}傾向への変化）",
                })
        
        # === 2. 移動平均の符号反転 ===
        if len(self.history) >= ALERT_MA_WINDOW:
            recent_scores = [h.get("total_score", 0) for h in self.history[-ALERT_MA_WINDOW:]]
            ma = sum(recent_scores) / len(recent_scores)
            prev_ma = sum([h.get("total_score", 0) for h in self.history[-(ALERT_MA_WINDOW+1):-1]]) / ALERT_MA_WINDOW if len(self.history) > ALERT_MA_WINDOW else None
            
            if prev_ma is not None:
                if ma >= 0 and prev_ma < 0:
                    alerts.append({
                        "type": "ma_reversal",
                        "severity": "info",
                        "message": f"{ALERT_MA_WINDOW}日移動平均がプラス圏に転換（市場センチメント改善の可能性）",
                    })
                elif ma < 0 and prev_ma >= 0:
                    alerts.append({
                        "type": "ma_reversal",
                        "severity": "warning",
                        "message": f"{ALERT_MA_WINDOW}日移動平均がマイナス圏に転換（市場センチメント悪化の可能性）",
                    })
        
        # === 3. 国内外スコア乖離 ===
        gap = current_scores.get("domestic_foreign_gap", 0)
        if abs(gap) >= ALERT_DOMESTIC_FOREIGN_GAP:
            if gap > 0:
                alerts.append({
                    "type": "domestic_foreign_gap",
                    "severity": "info",
                    "message": f"国内スコアが海外より {gap:+.1f} 高い（国内市場が海外より楽観的）",
                })
            else:
                alerts.append({
                    "type": "domestic_foreign_gap",
                    "severity": "warning",
                    "message": f"国内スコアが海外より {gap:.1f} 低い（国内市場が海外より悲観的）",
                })
        
        return alerts
    
    def get_moving_average(self, window: int = 3) -> Optional[float]:
        """移動平均を取得"""
        if len(self.history) < window:
            return None
        recent = [h.get("total_score", 0) for h in self.history[-window:]]
        return sum(recent) / len(recent)
