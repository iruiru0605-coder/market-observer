"""
マクロ環境観測モジュール

【重要】
- このモジュールは「観測」を目的とし、スコアには影響しない
- 為替・金利・経済指標を「前提条件として注視が必要」な情報として可視化
- 投資判断・売買示唆は禁止
"""
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class MacroObservation:
    """マクロ環境観測結果"""
    
    # 為替関連
    fx_news: List[Dict[str, Any]] = field(default_factory=list)
    fx_keywords: List[str] = field(default_factory=list)
    
    # 金利・国債関連
    rates_news: List[Dict[str, Any]] = field(default_factory=list)
    rates_keywords: List[str] = field(default_factory=list)
    
    # 経済指標関連
    data_news: List[Dict[str, Any]] = field(default_factory=list)
    data_keywords: List[str] = field(default_factory=list)
    
    @property
    def fx_count(self) -> int:
        return len(self.fx_news)
    
    @property
    def rates_count(self) -> int:
        return len(self.rates_news)
    
    @property
    def data_count(self) -> int:
        return len(self.data_news)
    
    @property
    def total_count(self) -> int:
        return self.fx_count + self.rates_count + self.data_count


class MacroObserver:
    """マクロ環境観測器"""
    
    # 為替関連キーワード
    FX_KEYWORDS = [
        "dollar", "yen", "usd/jpy", "exchange rate", "currency",
        "ドル", "円", "為替", "円安", "円高", "ドル高", "ドル安",
        "euro", "eur", "gbp", "pound",
    ]
    
    # 金利・国債関連キーワード
    RATES_KEYWORDS = [
        "treasury", "yield", "bond", "interest rate", "10-year",
        "国債", "金利", "利回り", "長期金利", "短期金利",
        "jgb", "bund", "gilt",
    ]
    
    # 経済指標関連キーワード
    DATA_KEYWORDS = [
        "cpi", "inflation", "jobs report", "employment", "gdp",
        "pce", "nonfarm payroll", "unemployment", "retail sales",
        "consumer price", "producer price", "pmi", "ism",
        "インフレ", "消費者物価", "雇用統計", "失業率",
    ]
    
    def observe(self, news_list: List[Dict[str, Any]]) -> MacroObservation:
        """
        ニュースリストからマクロ環境を観測
        """
        result = MacroObservation()
        
        for news in news_list:
            text = news.get("text", "").lower()
            
            # 為替チェック
            matched_fx = [kw for kw in self.FX_KEYWORDS if kw.lower() in text]
            if matched_fx:
                result.fx_news.append(news)
                result.fx_keywords.extend(matched_fx)
            
            # 金利チェック
            matched_rates = [kw for kw in self.RATES_KEYWORDS if kw.lower() in text]
            if matched_rates:
                result.rates_news.append(news)
                result.rates_keywords.extend(matched_rates)
            
            # 経済指標チェック
            matched_data = [kw for kw in self.DATA_KEYWORDS if kw.lower() in text]
            if matched_data:
                result.data_news.append(news)
                result.data_keywords.extend(matched_data)
        
        # 重複削除
        result.fx_keywords = list(set(result.fx_keywords))
        result.rates_keywords = list(set(result.rates_keywords))
        result.data_keywords = list(set(result.data_keywords))
        
        return result


def observe_macro(news_list: List[Dict[str, Any]]) -> MacroObservation:
    """マクロ環境を観測（簡易関数）"""
    observer = MacroObserver()
    return observer.observe(news_list)
