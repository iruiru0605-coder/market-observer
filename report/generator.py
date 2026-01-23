"""
レポート生成モジュール
日次市場観測レポートを生成

【重要】
- このレポートは「観測・状況整理」を目的とする
- 投資助言・売買示唆につながる表現は禁止
- +0 = 失敗ではなく「方向性を断定できない」状態
- 初心者でも理解できる平易な日本語を使用
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
    history_comparison: Optional[Dict[str, Any]] = None,
    triggers: Optional[List] = None,
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
    
    # スコア分布を計算
    plus2_count = sum(1 for n in scored_news_list if n.get("impact_score", 0) >= 2)
    minus2_count = sum(1 for n in scored_news_list if n.get("impact_score", 0) <= -2)
    
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
    
    # ===== 2. 今日の一言まとめ（新規追加） =====
    one_liner = _generate_one_liner(total, zero_ratio)
    report_lines.extend([
        f"📝 今日の一言まとめ",
        f"   {one_liner}",
        "",
    ])
    
    # ===== 3. 過去7日間との比較 =====
    if history_comparison and history_comparison.get("has_history"):
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【過去7日間との比較】                                  │",
            "└─────────────────────────────────────────────────────┘",
        ])
        
        days = history_comparison.get("days_count", 0)
        avg_total = history_comparison.get("avg_total_score", 0)
        avg_zero = history_comparison.get("avg_zero_ratio", 0)
        
        report_lines.append(f"   ※ 過去{days}日分のデータと比較しています")
        report_lines.append("")
        
        # 総合スコア比較
        report_lines.append(f"   ・過去{days}日平均の総合スコア: {avg_total:+.2f}")
        report_lines.append(f"   ・本日の総合スコア: {total:+.1f}")
        
        score_diff = total - avg_total
        if abs(score_diff) < 0.5:
            report_lines.append("   → 最近1週間と比べて、大きな変化はありません。")
        elif score_diff > 0:
            report_lines.append("   → 最近1週間と比べると、やや良いニュースが増えています。")
        else:
            report_lines.append("   → 最近1週間と比べると、やや慎重な評価が増えています。")
        
        report_lines.append("")
        
        # 評価保留比較
        report_lines.append("   ・評価保留（判断がつかないニュース）の割合")
        report_lines.append(f"     過去{days}日平均: {avg_zero:.0f}%")
        report_lines.append(f"     本日: {zero_ratio:.0f}%")
        
        zero_diff = zero_ratio - avg_zero
        if abs(zero_diff) < 10:
            report_lines.append("   → いつもと同じくらいです。")
        elif zero_diff > 0:
            report_lines.append("   → 今日は、判断材料として使いにくいニュースが多い日です。")
        else:
            report_lines.append("   → 今日は、判断しやすいニュースが多い日です。")
        
        report_lines.append("")
    
    # ===== 4. 観測メモ（トリガー） =====
    report_lines.extend([
        "┌─────────────────────────────────────────────────────┐",
        "│ 【観測メモ（自動検知）】                                │",
        "│ ※ニュースの分布から注目点だけを機械的に拾っています    │",
        "│   （売買判断ではありません）                            │",
        "└─────────────────────────────────────────────────────┘",
    ])
    
    if triggers:
        for trigger in triggers:
            msg = trigger.message if hasattr(trigger, 'message') else trigger.get('message', '')
            report_lines.append(f"   💡 {msg}")
    else:
        report_lines.append("   現在、特筆すべき観測メモはありません。")
    
    report_lines.append("")
    
    # ===== 5. 評価保留ニュースの内訳 =====
    zero_news = [n for n in scored_news_list if n.get("impact_score", 0) == 0]
    if zero_news:
        reason_counts = Counter(n.get("score_reason", "不明") for n in zero_news)
        
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【評価保留ニュースの内訳】                             │",
            "│ ※なぜ判断できないニュースが多いのかが分かります       │",
            "└─────────────────────────────────────────────────────┘",
        ])
        
        for reason, count in reason_counts.most_common():
            report_lines.append(f"   ・{reason}: {count}件")
        
        # まとめコメントを追加
        summary_comment = _generate_zero_summary(reason_counts)
        report_lines.append("")
        report_lines.append(f"   → {summary_comment}")
        report_lines.append("")
    
    # ===== 6. 変化点・アラート =====
    report_lines.append("【変化点・アラート】")
    if alerts:
        for alert in alerts:
            severity = "⚠️" if alert.get("severity") == "warning" else "ℹ️"
            report_lines.append(f"   {severity} {alert.get('message', '')}")
    else:
        report_lines.append("   特に大きな変化は見られませんでした。")
    report_lines.append("")
    
    # ===== 7. 国内外乖離 =====
    gap = aggregate_scores.get("domestic_foreign_gap", 0)
    report_lines.extend([
        "【国内と海外の比較】",
        f"   スコアの差: {gap:+.1f}",
    ])
    
    if abs(gap) < 2:
        gap_analysis = "国内と海外で、ニュースの受け止め方に大きな差はありません。"
    elif gap >= 2:
        gap_analysis = "国内の方が、海外より楽観的なニュースが多いようです。"
    else:
        gap_analysis = "国内の方が、海外より慎重なニュースが多いようです。"
    
    report_lines.extend([
        f"   {gap_analysis}",
        "",
    ])
    
    # ===== 8. シナリオ（注意書き追加） =====
    report_lines.extend([
        "【今後の可能性（参考）】",
        "※将来予測ではなく、「こういう見方もできる」という整理です",
    ])
    scenarios = _generate_scenarios(total, gap, alerts, zero_count, news_count)
    for i, scenario in enumerate(scenarios, 1):
        report_lines.append(f"   可能性{i}: {scenario}")
    report_lines.append("")
    
    # ===== 9. マクロ環境観測 =====
    if macro_observation and macro_observation.total_count > 0:
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【経済の大きな流れ（金利・為替・指標）】                │",
            "│ ※株価に直接影響しませんが、背景として重要です        │",
            "└─────────────────────────────────────────────────────┘",
        ])
        
        if macro_observation.fx_count > 0:
            report_lines.append(f"   📈 為替（ドル・円など）に関するニュース: {macro_observation.fx_count}件")
        
        if macro_observation.rates_count > 0:
            report_lines.append(f"   📉 金利・国債に関するニュース: {macro_observation.rates_count}件")
        
        if macro_observation.data_count > 0:
            report_lines.append(f"   📊 経済指標に関するニュース: {macro_observation.data_count}件")
        
        report_lines.append("")
    
    # ===== 10. 政治発言（整理表示） =====
    if political_events:
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【重要人物の発言（参考情報）】                         │",
            "│ ※スコアには影響していません                          │",
            "└─────────────────────────────────────────────────────┘",
        ])
        
        # 発言者ごとにグループ化
        grouped = _group_political_events(political_events)
        
        for speaker, data in grouped.items():
            themes = ", ".join([f"{t}（{c}件）" for t, c in data["themes"].items()])
            summaries = list(set(data["summaries"]))[:3]
            sources = ", ".join(list(set(data["sources"]))[:3])
            
            report_lines.append(f"   - 発言者: {speaker}")
            report_lines.append(f"     主なテーマ: {themes}")
            report_lines.append(f"     発言要旨:")
            for s in summaries:
                report_lines.append(f"       ・{s}")
            report_lines.append(f"     主な情報源: {sources}")
            report_lines.append("")
    
    # ===== 11. 注意点 =====
    report_lines.extend([
        "【このレポートについて】",
        "   ・このレポートは情報をまとめたものであり、投資のアドバイスではありません。",
        "   ・「判断できない」ニュースが多いことは、失敗ではなく正常な状態です。",
        "   ・最終的な判断は、ご自身の責任でお願いいたします。",
        "",
        "=" * 60,
    ])
    
    report = "\n".join(report_lines)
    
    # ===== 12. 詳細ニュース一覧 =====
    detail_lines = [
        "",
        "┌─────────────────────────────────────────────────────┐",
        "│ 【詳細ニュース一覧】                                    │",
        "│ ※ ★ はスコアに影響したニュースです                     │",
        "│   （良し悪しの判断ではありません）                       │",
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


def _generate_one_liner(total: float, zero_ratio: float) -> str:
    """今日の一言まとめを生成"""
    if zero_ratio >= 70:
        return "今日は「判断材料が少なく、方向性を決めにくい日」です。"
    elif zero_ratio >= 50:
        return "今日は「はっきりしたニュースが少なめの日」です。"
    elif total >= 3:
        return "今日は「良いニュースが目立つ日」です。"
    elif total >= 1:
        return "今日は「やや良いニュースがある日」です。"
    elif total <= -3:
        return "今日は「心配なニュースが目立つ日」です。"
    elif total <= -1:
        return "今日は「やや気になるニュースがある日」です。"
    else:
        return "今日は「特に大きな動きがない日」です。"


def _generate_zero_summary(reason_counts: Counter) -> str:
    """評価保留の内訳まとめコメントを生成"""
    top_reason = reason_counts.most_common(1)[0][0] if reason_counts else ""
    
    if "定性的情報" in top_reason or "価格材料不足" in top_reason:
        return "今日は「話題は多いが、市場全体の判断材料になりにくいニュース」が中心でした。"
    elif "市場全体への波及" in top_reason:
        return "今日は「個別の話題が多く、市場全体への影響が見えにくいニュース」が中心でした。"
    elif "個別" in top_reason or "話題性" in top_reason:
        return "今日は「話題性のあるニュースが多いが、市場への影響は限定的」な状況でした。"
    else:
        return "今日は「判断に使いにくいニュースが多い」状況でした。"


def _group_political_events(events: List) -> Dict[str, Any]:
    """政治発言を発言者ごとにグループ化"""
    grouped = {}
    
    for event in events:
        event_dict = event.to_dict() if hasattr(event, 'to_dict') else event
        speaker = event_dict.get("speaker", "不明")
        
        if speaker not in grouped:
            grouped[speaker] = {
                "themes": Counter(),
                "summaries": [],
                "sources": [],
            }
        
        context = event_dict.get("context", "その他")
        grouped[speaker]["themes"][context] += 1
        grouped[speaker]["summaries"].append(event_dict.get("summary", ""))
        grouped[speaker]["sources"].append(event_dict.get("source_name", ""))
    
    return grouped


def _generate_scenarios(total_score: float, gap: float, alerts: List, zero_count: int, news_count: int) -> List[str]:
    """シナリオを生成（安全な表現）"""
    scenarios = []
    
    if news_count > 0 and zero_count / news_count > 0.5:
        scenarios.append("はっきりしたニュースが出るまで、動きが少ない状態が続く可能性があります。")
        scenarios.append("新しいニュースが出れば、方向性が見えてくる可能性があります。")
    elif total_score >= 3:
        scenarios.append("良いニュースが続けば、しばらく良い流れが続く可能性があります。")
        scenarios.append("一度調整が入る可能性もあります。")
    elif total_score <= -3:
        scenarios.append("悪いニュースが一段落すれば、回復の動きが出る可能性があります。")
        scenarios.append("さらに気になるニュースが続く可能性もあります。")
    else:
        scenarios.append("新しいニュースを待つ状態が続く可能性があります。")
        scenarios.append("何か大きなニュースが出れば、方向性が決まる可能性があります。")
    
    return scenarios[:2]
