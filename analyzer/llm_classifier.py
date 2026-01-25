"""
LLMベースのニュース分類・スコアリングモジュール

Gemini APIを使用して:
1. ニュースの分類（市場全体/セクター/テーマ）
2. 投資インパクトスコアの算出
3. 類似記事の検出・重複排除
"""
import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# Gemini APIの初期化
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


@dataclass
class LLMClassificationResult:
    """LLM分類結果（詳細版）"""
    category: str  # market, sector, theme
    sub_category: Optional[str]
    impact_score: int  # -10 to +10（総合スコア）
    
    # 詳細スコア（各観点）
    market_impact: int       # 市場全体への影響度 (-10〜+10)
    time_horizon: str        # short/medium/long（影響の時間軸）
    confidence: int          # 評価の確信度 (1-5)
    
    # 詳細な理由
    reason: str              # 総合判定理由
    positive_factors: List[str]  # プラス要因リスト
    negative_factors: List[str]  # マイナス要因リスト
    uncertainty_factors: List[str]  # 不確実要因リスト
    
    keywords: List[str]
    content_hash: str  # 重複検出用


class GeminiClassifier:
    """Gemini APIを使用したニュース分類器（詳細評価版）"""
    
    SYSTEM_PROMPT = """あなたは大手証券会社に20年以上勤務するシニア証券アナリストです。

【あなたのプロフィール】
- CFA（米国証券アナリスト）資格保持者
- 日本および米国市場の両方に精通
- マクロ経済、金融政策、為替、株式市場を専門とする
- 機関投資家向けレポートを日々執筆している
- 冷静かつ客観的な分析を心がけ、感情的な判断を避ける

【分析姿勢】
- 市場の短期的なノイズと、本質的な変化を区別する
- 「織り込み済み」かどうかを常に意識する
- 過去の類似事例との比較を行う
- 確証バイアスを避け、反対意見も検討する
- 不確実性を正直に認める

【分類カテゴリ】
- market: 市場全体に影響（金融政策、GDP、雇用統計など）
- sector: 特定セクターに影響（テクノロジー、金融、自動車など）
- theme: テーマ別（地政学リスク、M&A、決算など）

【投資インパクトスコア評価基準】（-10〜+10）
■ 極めて強い影響 (±7〜±10)
  - 中央銀行の想定外の政策変更（利上げ/利下げサプライズ）
  - 大規模な金融危機・システミックリスク
  - 主要企業の破綻・超大型M&A

■ 強い影響 (±4〜±6)
  - 重要経済指標の予想外の結果（雇用統計、CPI等）
  - 大手企業の業績大幅修正・ガイダンス変更
  - 重大な地政学イベント（戦争、制裁等）

■ 中程度の影響 (±2〜±3)
  - 経済指標が予想通りの結果
  - 中堅企業の業績発表
  - セクター固有のニュース
  - すでに市場に「織り込み済み」の材料

■ 軽微な影響 (±1)
  - 日常的な市場コメント
  - 小規模な企業ニュース
  - 憶測や噂レベルの報道

■ 中立・判断困難 (0)
  - 情報が不十分で判断できない
  - プラスとマイナスが相殺される
  - 市場への影響が読めない

【時間軸】
- short: 数日〜1週間（イベントドリブン）
- medium: 1週間〜1ヶ月（トレンド形成）
- long: 1ヶ月以上（構造的変化）

【確信度】(1-5)
- 5: 確定的な事実に基づく（公式発表等）
- 4: 高い確信（信頼できるソース）
- 3: 中程度の確信（複数ソース）
- 2: 低い確信（単一ソース・速報）
- 1: 推測が多い（噂・観測報道）

【プロとしての重要ルール】
- 「買い」「売り」の直接的な推奨は行わない
- 必ずプラス面とマイナス面の両方を検討する
- 不確実な要素は明示し、過信を避ける
- 感情的・扇情的な表現を避け、冷静に分析する
- 市場参加者がどう反応するかを考慮する

JSON形式で回答:
{
  "category": "market|sector|theme",
  "sub_category": "セクター名またはテーマ名（なければnull）",
  "impact_score": 数値(-10〜+10),
  "market_impact": 数値(-10〜+10),
  "time_horizon": "short|medium|long",
  "confidence": 数値(1-5),
  "reason": "プロの視点からの総合判定理由（日本語、100字以内）",
  "positive_factors": ["プラス要因1", "プラス要因2"],
  "negative_factors": ["マイナス要因1", "マイナス要因2"],
  "uncertainty_factors": ["不確実要因1"],
  "keywords": ["重要キーワード1", "キーワード2"]
}"""

    def __init__(self, api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai がインストールされていません")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY が設定されていません")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        
        # 類似記事検出用のキャッシュ
        self.seen_hashes: Dict[str, Dict[str, Any]] = {}
    
    def _compute_content_hash(self, text: str) -> str:
        """コンテンツのハッシュを計算（類似検出用）"""
        # 小文字化して主要単語のみ抽出
        words = sorted(set(text.lower().split()))[:20]
        return hashlib.md5(" ".join(words).encode()).hexdigest()[:12]
    
    def _is_similar(self, text: str, threshold: float = 0.6) -> Optional[Dict[str, Any]]:
        """類似記事があるかチェック"""
        new_words = set(text.lower().split())
        
        for hash_key, cached in self.seen_hashes.items():
            cached_words = set(cached.get("words", []))
            if not cached_words:
                continue
            
            # Jaccard係数で類似度計算
            intersection = len(new_words & cached_words)
            union = len(new_words | cached_words)
            
            if union > 0 and intersection / union >= threshold:
                return cached
        
        return None
    
    def classify_single(self, news_text: str, source_name: str = "") -> LLMClassificationResult:
        """単一ニュースを詳細分類"""
        content_hash = self._compute_content_hash(news_text)
        
        # 類似記事チェック
        similar = self._is_similar(news_text)
        if similar:
            return LLMClassificationResult(
                category=similar["category"],
                sub_category=similar.get("sub_category"),
                impact_score=similar["impact_score"],
                market_impact=similar.get("market_impact", similar["impact_score"]),
                time_horizon=similar.get("time_horizon", "medium"),
                confidence=similar.get("confidence", 3),
                reason=f"[類似記事] {similar['reason']}",
                positive_factors=similar.get("positive_factors", []),
                negative_factors=similar.get("negative_factors", []),
                uncertainty_factors=similar.get("uncertainty_factors", []),
                keywords=similar.get("keywords", []),
                content_hash=content_hash,
            )
        
        # Gemini APIで分類
        try:
            prompt = f"{self.SYSTEM_PROMPT}\n\n【ニュース】\n{news_text[:1500]}"
            response = self.model.generate_content(prompt)
            
            # JSONパース
            response_text = response.text.strip()
            # ```json ... ``` を除去
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            result = json.loads(response_text)
            
            # キャッシュに保存（詳細フィールド含む）
            self.seen_hashes[content_hash] = {
                "category": result.get("category", "market"),
                "sub_category": result.get("sub_category"),
                "impact_score": result.get("impact_score", 0),
                "market_impact": result.get("market_impact", result.get("impact_score", 0)),
                "time_horizon": result.get("time_horizon", "medium"),
                "confidence": result.get("confidence", 3),
                "reason": result.get("reason", ""),
                "positive_factors": result.get("positive_factors", []),
                "negative_factors": result.get("negative_factors", []),
                "uncertainty_factors": result.get("uncertainty_factors", []),
                "keywords": result.get("keywords", []),
                "words": list(set(news_text.lower().split()))[:30],
            }
            
            return LLMClassificationResult(
                category=result.get("category", "market"),
                sub_category=result.get("sub_category"),
                impact_score=max(-10, min(10, result.get("impact_score", 0))),
                market_impact=max(-10, min(10, result.get("market_impact", result.get("impact_score", 0)))),
                time_horizon=result.get("time_horizon", "medium"),
                confidence=max(1, min(5, result.get("confidence", 3))),
                reason=result.get("reason", "LLM分類"),
                positive_factors=result.get("positive_factors", []),
                negative_factors=result.get("negative_factors", []),
                uncertainty_factors=result.get("uncertainty_factors", []),
                keywords=result.get("keywords", []),
                content_hash=content_hash,
            )
            
        except Exception as e:
            # フォールバック
            return LLMClassificationResult(
                category="market",
                sub_category=None,
                impact_score=0,
                market_impact=0,
                time_horizon="medium",
                confidence=1,
                reason=f"LLMエラー: {str(e)[:30]}",
                positive_factors=[],
                negative_factors=[],
                uncertainty_factors=["API呼び出しに失敗"],
                keywords=[],
                content_hash=content_hash,
            )
    
    def classify_batch(self, news_list: List[Dict[str, Any]], 
                       max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """複数ニュースをバッチ分類（詳細評価付き）"""
        results = []
        
        for news in news_list:
            text = news.get("text", news.get("title", ""))
            source = news.get("source_name", "")
            
            classification = self.classify_single(text, source)
            
            # 元のニュース情報とマージ（詳細フィールド含む）
            result = news.copy()
            result.update({
                "category": classification.category,
                "sub_category": classification.sub_category,
                "impact_score": classification.impact_score,
                "market_impact": classification.market_impact,
                "time_horizon": classification.time_horizon,
                "confidence": classification.confidence,
                "score_reason": classification.reason,
                "positive_factors": classification.positive_factors,
                "negative_factors": classification.negative_factors,
                "uncertainty_factors": classification.uncertainty_factors,
                "keywords": classification.keywords,
                "content_hash": classification.content_hash,
            })
            results.append(result)
        
        return results
    
    def get_dedup_stats(self) -> Dict[str, int]:
        """重複検出の統計を取得"""
        return {
            "unique_articles": len(self.seen_hashes),
            "cached_hashes": len(self.seen_hashes),
        }


def classify_with_llm(news_list: List[Dict[str, Any]], 
                      api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """LLMでニュースを分類（簡易関数）"""
    try:
        classifier = GeminiClassifier(api_key)
        return classifier.classify_batch(news_list)
    except Exception as e:
        print(f"LLM分類エラー: {e}")
        # フォールバック: 元のデータを返す
        return news_list
