"""
レポート生成モジュール
日次市場観測レポートを生成

【重要】
- このレポートは「観測・状況整理」を目的とする
- 投資助言・売買示唆につながる表現は禁止
- +0 = 失敗ではなく「方向性を断定できない」状態
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import Counter
from config import get_log_filename


def generate_report(
    scored_news_list: List[Dict[str, Any]],
    aggregate_scores: Dict[str, Any],
    alerts: List[Dict[str, str]],
    political_events: Optional[List] = None,
    macro_observation = None,
    save_to_file: bool = True
) -> str:
    """
    日次市場観測レポートを生成
    """
    now = datetime.now()
    news_count = aggregate_scores.get("news_count", 0)
    zero_count = aggregate_scores.get("zero_score_count", 0)
    zero_ratio = (zero_count / news_count * 100) if news_count > 0 else 0
    total = aggregate_scores.get("total_score", 0)
    
    # ===== ヘッダー =====
    report_lines = [
        "=" * 60,
        "📊 日次市場観測レポート",
        f"   生成日時: {now.strftime('%Y年%m月%d日 %H:%M')}",
        "=" * 60,
        "",
    ]
    
    # ===== 1. サマリー =====
    report_lines.extend([
        "┌─────────────────────────────────────────────────────┐",
        "│ 【サマリー】                                          │",
        "├─────────────────────────────────────────────────────┤",
        f"│  総合スコア: {total:+.1f}                                      │",
        f"│  国内: {aggregate_scores.get('domestic_score', 0):+.1f}  /  海外: {aggregate_scores.get('foreign_score', 0):+.1f}                         │",
        f"│  分析ニュース数: {news_count}件                               │",
        f"│  評価保留（±0）: {zero_count} / {news_count} 件（約{zero_ratio:.0f}%）              │",
        "└─────────────────────────────────────────────────────┘",
        "",
    ])
    
    # 状況解釈
    if zero_ratio >= 50:
        situation = "過半数が評価保留 → 方向性判断は困難な状態"
        explanation = "現時点では材料が出揃っていません。方向性確定には追加情報が必要です。"
    elif total >= 5:
        situation = "ポジティブ材料が優勢"
        explanation = "好材料が多く検出されています。"
    elif total >= 2:
        situation = "やや好材料が多い状況"
        explanation = "一部に好材料が見られます。"
    elif total <= -5:
        situation = "ネガティブ材料が優勢"
        explanation = "懸念材料が多く検出されています。"
    elif total <= -2:
        situation = "やや懸念材料が多い状況"
        explanation = "一部に懸念材料が見られます。"
    else:
        situation = "平常レンジ内（材料混在）"
        explanation = "好悪材料が混在しており、明確な方向性は見出しにくい状況です。"
    
    report_lines.extend([
        f"📍 状況: {situation}",
        f"   {explanation}",
        "",
    ])
    
    # ===== 2. 評価保留ニュースの内訳 =====
    zero_news = [n for n in scored_news_list if n.get("impact_score", 0) == 0]
    if zero_news:
        reason_counts = Counter(n.get("score_reason", "不明") for n in zero_news)
        
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【評価保留ニュースの内訳】                             │",
            "└─────────────────────────────────────────────────────┘",
        ])
        
        for reason, count in reason_counts.most_common():
            report_lines.append(f"   ・{reason}: {count}件")
        report_lines.append("")
    
    # ===== 3. 変化点・アラート =====
    report_lines.append("【変化点・アラート】")
    if alerts:
        for alert in alerts:
            severity = "⚠️" if alert.get("severity") == "warning" else "ℹ️"
            report_lines.append(f"   {severity} {alert.get('message', '')}")
    else:
        report_lines.append("   特筆すべき変化点は検出されませんでした")
    report_lines.append("")
    
    # ===== 4. 国内外乖離 =====
    gap = aggregate_scores.get("domestic_foreign_gap", 0)
    report_lines.extend([
        "【国内外乖離分析】",
        f"   乖離幅: {gap:+.1f}",
    ])
    
    if abs(gap) < 2:
        gap_analysis = "国内外で市場認識に大きな差異なし"
    elif gap >= 2:
        gap_analysis = "国内市場が海外より楽観的な傾向"
    else:
        gap_analysis = "国内市場が海外より悲観的な傾向"
    
    report_lines.extend([
        f"   分析: {gap_analysis}",
        "",
    ])
    
    # ===== 5. シナリオ =====
    report_lines.append("【考えられるシナリオ】")
    scenarios = _generate_scenarios(total, gap, alerts, zero_count, news_count)
    for i, scenario in enumerate(scenarios, 1):
        report_lines.append(f"   シナリオ{i}: {scenario}")
    report_lines.append("")
    
    # ===== 6. マクロ環境観測 =====
    if macro_observation and macro_observation.total_count > 0:
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【マクロ環境観測（為替・金利・指標）】                   │",
            "│ ※スコアに直接影響なし・前提条件として注視が必要        │",
            "└─────────────────────────────────────────────────────┘",
        ])
        
        if macro_observation.fx_count > 0:
            kws = ", ".join(macro_observation.fx_keywords[:3])
            report_lines.append(f"   📈 為替関連: {macro_observation.fx_count}件 ({kws})")
        
        if macro_observation.rates_count > 0:
            kws = ", ".join(macro_observation.rates_keywords[:3])
            report_lines.append(f"   📉 金利・国債関連: {macro_observation.rates_count}件 ({kws})")
        
        if macro_observation.data_count > 0:
            kws = ", ".join(macro_observation.data_keywords[:3])
            report_lines.append(f"   📊 経済指標関連: {macro_observation.data_count}件 ({kws})")
        
        report_lines.append("")
    
    # ===== 7. 政治発言・市場感応イベント =====
    if political_events:
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【参考：政治発言・市場感応イベント】                    │",
            "│ ※スコア付与なし・総合スコアに影響なし                  │",
            "└─────────────────────────────────────────────────────┘",
        ])
        for event in political_events:
            event_dict = event.to_dict() if hasattr(event, 'to_dict') else event
            report_lines.extend([
                f"   - 発言者: {event_dict.get('speaker', '不明')}",
                f"     要旨: {event_dict.get('summary', '不明')}",
                f"     文脈: {event_dict.get('context', '不明')}",
                f"     初出ソース: {event_dict.get('source_name', '不明')}",
                f"     市場評価: {event_dict.get('evaluation', '未評価')}",
                "",
            ])
    report_lines.append("")
    
    # ===== 8. 注意点 =====
    report_lines.extend([
        "【注意点】",
        "   ・本レポートは情報整理を目的としており、投資助言ではありません",
        "   ・スコアは過去材料の定量化であり、将来を予測するものではありません",
        "   ・評価保留（±0）は「判断できない」状態を示し、失敗ではありません",
        "   ・最終的な判断は利用者ご自身でお願いいたします",
        "",
        "=" * 60,
    ])
    
    report = "\n".join(report_lines)
    
    # ===== 9. 詳細ニュース一覧 =====
    detail_lines = [
        "",
        "┌─────────────────────────────────────────────────────┐",
        "│ 【詳細ニュース一覧】                                    │",
        "└─────────────────────────────────────────────────────┘",
    ]
    
    for news in scored_news_list:
        score = news.get('impact_score', 0)
        reason = news.get('score_reason', '理由なし')
        category = news.get('category_name', '-')
        sub = f" ({news['sub_category']})" if news.get("sub_category") else ""
        source = news.get('source', '-')
        text = news.get('text', '')[:100]
        
        # スコア変動マーク（±2以上）
        mark = " ★" if abs(score) >= 2 else ""
        
        detail_lines.extend([
            "",
            f"[{source}] スコア: {score:+d}{mark}",
            f"  分類: {category}{sub}",
            f"  判定理由: {reason}",
            f"  内容: {text}...",
        ])
    
    details = "\n".join(detail_lines)
    
    # ファイル保存
    if save_to_file:
        log_path = get_log_filename()
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(report)
            f.write(details)
        print(f"\n📁 レポート保存: {log_path}")
    
    return report + details


def _generate_scenarios(total_score: float, gap: float, alerts: List, zero_count: int, news_count: int) -> List[str]:
    """シナリオを生成（2-3つ）"""
    scenarios = []
    
    if news_count > 0 and zero_count / news_count > 0.5:
        scenarios.append("明確な材料が出るまでレンジ推移となる可能性")
        scenarios.append("新たな材料をきっかけに方向感が出る可能性")
    elif total_score >= 3:
        scenarios.append("好材料が継続し、短期的に堅調な展開が続く可能性")
        scenarios.append("利益確定売りが出やすく、調整を挟む可能性")
    elif total_score <= -3:
        scenarios.append("悪材料が一巡し、反発の動きが出る可能性")
        scenarios.append("追加の悪材料で下値を試す展開となる可能性")
    else:
        scenarios.append("材料待ちでレンジ推移となる可能性")
        scenarios.append("新たな材料をきっかけに方向感が出る可能性")
    
    if abs(gap) >= 3:
        if gap > 0:
            scenarios.append("海外市場の改善を受け、国内が追随して上昇する可能性")
        else:
            scenarios.append("海外市場の悪化を織り込み、国内が調整する可能性")
    
    return scenarios[:3]
