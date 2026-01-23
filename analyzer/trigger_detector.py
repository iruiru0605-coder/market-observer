"""
トリガー（観測メモ）検知モジュール

【重要】
- トリガーは売買や判断を促さない
- 総合スコアとは完全に独立
- 出た／出ないを事実として表示するのみ
"""
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class Trigger:
    """観測メモ"""
    id: str
    name: str
    message: str
    fired: bool = False


class TriggerDetector:
    """トリガー検知器"""
    
    def detect(
        self,
        zero_ratio: float,
        plus2_ratio: float,
        minus2_ratio: float,
        macro_ratio: float,
        consecutive_high_zero_days: int
    ) -> List[Trigger]:
        """
        トリガーを検知
        
        Args:
            zero_ratio: 評価保留（±0）の割合（%）
            plus2_ratio: +2以上の割合（%）
            minus2_ratio: -2以下の割合（%）
            macro_ratio: マクロ関連ニュースの割合（%）
            consecutive_high_zero_days: 評価保留80%超の連続日数
        
        Returns:
            発火したトリガーのリスト
        """
        triggers = []
        
        # トリガーA: 材料出揃いの兆候
        trigger_a = Trigger(
            id="A",
            name="材料出揃いの兆候",
            message="市場が評価可能な材料に反応し始めている可能性があります。"
        )
        if zero_ratio < 50 and (plus2_ratio > 30 or minus2_ratio > 30):
            trigger_a.fired = True
            triggers.append(trigger_a)
        
        # トリガーB: ノイズ優勢状態
        trigger_b = Trigger(
            id="B",
            name="ノイズ優勢状態",
            message="判断材料として使いにくいニュースが多い状態が続いています。"
        )
        if zero_ratio > 80 and consecutive_high_zero_days >= 2:
            trigger_b.fired = True
            triggers.append(trigger_b)
        
        # トリガーC: 評価の偏り
        trigger_c = Trigger(
            id="C",
            name="評価の偏り",
            message="市場の受け止め方が一方向に偏っている可能性があります。"
        )
        if plus2_ratio > 50 or minus2_ratio > 50:
            trigger_c.fired = True
            triggers.append(trigger_c)
        
        # トリガーD: マクロ前提変化
        trigger_d = Trigger(
            id="D",
            name="マクロ前提変化",
            message="株価以外の前提条件（金利・為替など）への注目が高まっています。"
        )
        if macro_ratio > 30:
            trigger_d.fired = True
            triggers.append(trigger_d)
        
        return triggers


def detect_triggers(
    zero_ratio: float,
    plus2_ratio: float,
    minus2_ratio: float,
    macro_ratio: float,
    consecutive_high_zero_days: int = 0
) -> List[Trigger]:
    """トリガーを検知（簡易関数）"""
    detector = TriggerDetector()
    return detector.detect(
        zero_ratio, plus2_ratio, minus2_ratio, 
        macro_ratio, consecutive_high_zero_days
    )
