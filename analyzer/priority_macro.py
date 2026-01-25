"""
最優先マクロ検知モジュール

【重要】
- 金利・為替・主要経済指標は「判断の土台」として最優先
- ニュースの量ではなく「有無」自体が意味を持つ
- スコアロジックは変更しない
"""
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class PriorityMacro:
    """最優先マクロ情報"""
    
    # 金利関連
    fed_news: List[Dict[str, Any]] = field(default_factory=list)
    treasury_news: List[Dict[str, Any]] = field(default_factory=list)
    
    # 為替関連
    usdjpy_news: List[Dict[str, Any]] = field(default_factory=list)
    dxy_news: List[Dict[str, Any]] = field(default_factory=list)
    
    # 主要経済指標
    employment_news: List[Dict[str, Any]] = field(default_factory=list)
    inflation_news: List[Dict[str, Any]] = field(default_factory=list)
    ism_news: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def has_fed(self) -> bool:
        return len(self.fed_news) > 0
    
    @property
    def has_treasury(self) -> bool:
        return len(self.treasury_news) > 0
    
    @property
    def has_usdjpy(self) -> bool:
        return len(self.usdjpy_news) > 0
    
    @property
    def has_employment(self) -> bool:
        return len(self.employment_news) > 0
    
    @property
    def has_inflation(self) -> bool:
        return len(self.inflation_news) > 0
    
    @property
    def has_ism(self) -> bool:
        return len(self.ism_news) > 0
    
    @property
    def has_any(self) -> bool:
        return (self.has_fed or self.has_treasury or self.has_usdjpy or 
                self.has_employment or self.has_inflation or self.has_ism)
    
    @property
    def total_count(self) -> int:
        return (len(self.fed_news) + len(self.treasury_news) + 
                len(self.usdjpy_news) + len(self.dxy_news) +
                len(self.employment_news) + len(self.inflation_news) + 
                len(self.ism_news))


class PriorityMacroDetector:
    """最優先マクロ検知器"""
    
    # FRB関連キーワード
    FED_KEYWORDS = [
        "federal reserve", "fed", "frb", "fomc",
        "powell", "パウエル", "連邦準備", "中央銀行",
        "rate decision", "金利決定",
    ]
    
    # 米国債利回りキーワード
    TREASURY_KEYWORDS = [
        "treasury yield", "10-year yield", "2-year yield",
        "bond yield", "米国債", "利回り", "長期金利",
    ]
    
    # USD/JPYキーワード（為替介入・レートチェック含む）
    USDJPY_KEYWORDS = [
        "usd/jpy", "dollar yen", "ドル円", "円安", "円高",
        "yen", "円", "usdjpy",
        # 為替介入関連
        "rate check", "レートチェック", "forex intervention", "為替介入",
        "intervention", "介入警戒", "口先介入", "verbal intervention",
        "boj intervention", "日銀介入", "mof intervention", "財務省介入",
        "kanda", "神田財務官", "三者会合",
    ]
    
    # DXYキーワード
    DXY_KEYWORDS = [
        "dollar index", "dxy", "ドル指数",
    ]
    
    # 雇用関連キーワード
    EMPLOYMENT_KEYWORDS = [
        "nonfarm payroll", "payroll", "雇用統計", 
        "jobs report", "unemployment", "失業率",
        "employment", "jobless claims",
    ]
    
    # 物価関連キーワード
    INFLATION_KEYWORDS = [
        "cpi", "consumer price", "消費者物価",
        "pce", "pce deflator", "inflation", "インフレ",
        "producer price", "ppi",
    ]
    
    # ISM関連キーワード
    ISM_KEYWORDS = [
        "ism", "pmi", "景況感", "manufacturing",
        "services pmi", "製造業景況",
    ]
    
    def detect(self, news_list: List[Dict[str, Any]]) -> PriorityMacro:
        """最優先マクロを検知"""
        result = PriorityMacro()
        
        for news in news_list:
            text = news.get("text", "").lower()
            
            # FRB
            if any(kw.lower() in text for kw in self.FED_KEYWORDS):
                result.fed_news.append(news)
            
            # 米国債
            if any(kw.lower() in text for kw in self.TREASURY_KEYWORDS):
                result.treasury_news.append(news)
            
            # USD/JPY
            if any(kw.lower() in text for kw in self.USDJPY_KEYWORDS):
                result.usdjpy_news.append(news)
            
            # DXY
            if any(kw.lower() in text for kw in self.DXY_KEYWORDS):
                result.dxy_news.append(news)
            
            # 雇用
            if any(kw.lower() in text for kw in self.EMPLOYMENT_KEYWORDS):
                result.employment_news.append(news)
            
            # 物価
            if any(kw.lower() in text for kw in self.INFLATION_KEYWORDS):
                result.inflation_news.append(news)
            
            # ISM
            if any(kw.lower() in text for kw in self.ISM_KEYWORDS):
                result.ism_news.append(news)
        
        return result


def detect_priority_macro(news_list: List[Dict[str, Any]]) -> PriorityMacro:
    """最優先マクロを検知（簡易関数）"""
    detector = PriorityMacroDetector()
    return detector.detect(news_list)
