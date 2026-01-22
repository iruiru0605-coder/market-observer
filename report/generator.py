"""
レポート生成モジュール
日次市場観測レポートを生成

【重要】
- このレポートは「観測・状況整理」を目的とする
- 投資助言・売買示唆につながる表現は禁止
- +0 = 失敗ではなく「方向性を断定できない」状態
"""
from datetime import datetime
from typing import Dict, Any, List
from config import get_log_filename


def generate_report(
    scored_news_list: List[Dict[str, Any]],
    aggregate_scores: Dict[str, Any],
    alerts: List[Dict[str, str]],
    save_to_file: bool = True
) -> str:
    """
    日次市場観測レポートを生成
    
    構成:
    - 総合スコア
    - 変化点
    - 国内外乖離
    - 考えられるシナリオ（複数）
    - 注意点
    """
    now = datetime.now()
    
    report_lines = [
        "=" * 60,
        f"📊 日次市場観測レポート",
        f"   生成日時: {now.strftime('%Y年%m月%d日 %H:%M')}",
        "=" * 60,
        "",
        "【1. 総合スコア】",
        f"   総合: {aggregate_scores.get('total_score', 0):+.1f}",
        f"   国内: {aggregate_scores.get('domestic_score', 0):+.1f}",
        f"   海外: {aggregate_scores.get('foreign_score', 0):+.1f}",
        f"   分析ニュース数: {aggregate_scores.get('news_count', 0)}件",
        f"   評価保留（±0）: {aggregate_scores.get('zero_score_count', 0)}件",
        "",
    ]
    
    # スコア解釈（観測・状況整理トーン）
    total = aggregate_scores.get("total_score", 0)
    zero_count = aggregate_scores.get("zero_score_count", 0)
    news_count = aggregate_scores.get("news_count", 0)
    
    if total >= 5:
        interpretation = "市場はポジティブ材料が優勢と観測される状況"
    elif total >= 2:
        interpretation = "やや好材料が多い状況"
    elif total <= -5:
        interpretation = "市場はネガティブ材料が優勢と観測される状況"
    elif total <= -2:
        interpretation = "やや悪材料が多い状況"
    else:
        interpretation = "平常レンジ内（材料混在または方向性不明確）"
    
    report_lines.extend([
        f"   状況: {interpretation}",
    ])
    
    # 評価保留が多い場合の補足
    if news_count > 0 and zero_count / news_count > 0.5:
        report_lines.append(f"   備考: 分析対象の過半数が評価保留となっており、明確な方向性が見出しにくい状況")
    
    report_lines.append("")
    
    # 変化点（アラート）
    report_lines.append("【2. 変化点・アラート】")
    if alerts:
        for alert in alerts:
            severity = "⚠️" if alert.get("severity") == "warning" else "ℹ️"
            report_lines.append(f"   {severity} {alert.get('message', '')}")
    else:
        report_lines.append("   特筆すべき変化点は検出されませんでした")
    report_lines.append("")
    
    # 国内外乖離
    gap = aggregate_scores.get("domestic_foreign_gap", 0)
    report_lines.extend([
        "【3. 国内外乖離分析】",
        f"   乖離幅: {gap:+.1f}",
    ])
    
    if abs(gap) < 2:
        gap_analysis = "国内外で市場認識に大きな差異なし"
    elif gap >= 2:
        gap_analysis = "国内市場が海外より楽観的な傾向。海外リスクへの警戒を考慮"
    else:
        gap_analysis = "国内市場が海外より悲観的な傾向。海外の好材料が未反映の可能性"
    
    report_lines.extend([
        f"   分析: {gap_analysis}",
        "",
    ])
    
    # シナリオ整理（非指示・複数提示）
    report_lines.append("【4. 考えられるシナリオ】")
    scenarios = _generate_scenarios(total, gap, alerts, zero_count, news_count)
    for i, scenario in enumerate(scenarios, 1):
        report_lines.append(f"   シナリオ{i}: {scenario}")
    report_lines.append("")
    
    # 注意点
    report_lines.extend([
        "【5. 注意点】",
        "   ・本レポートは情報整理を目的としており、投資助言ではありません",
        "   ・スコアは過去材料の定量化であり、将来を予測するものではありません",
        "   ・評価保留（±0）は「判断できない」状態を示し、失敗ではありません",
        "   ・最終的な判断は利用者ご自身でお願いいたします",
        "",
        "=" * 60,
    ])
    
    report = "\n".join(report_lines)
    
    # ファイル保存
    if save_to_file:
        log_path = get_log_filename()
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(report)
            f.write("\n\n--- 詳細ニュース一覧 ---\n")
            for news in scored_news_list:
                score = news.get('impact_score', 0)
                reason = news.get('score_reason', '理由なし')
                f.write(f"\n[{news.get('source', '-')}] スコア:{score:+d}\n")
                f.write(f"  分類: {news.get('category_name', '-')}")
                if news.get("sub_category"):
                    f.write(f" ({news['sub_category']})")
                f.write(f"\n  判定理由: {reason}\n")
                f.write(f"  内容: {news.get('text', '')[:150]}...\n")
        print(f"\n📁 レポート保存: {log_path}")
    
    # コンソール出力用に詳細も追加
    report += "\n\n--- 詳細ニュース一覧 ---\n"
    for news in scored_news_list:
        score = news.get('impact_score', 0)
        reason = news.get('score_reason', '理由なし')
        report += f"\n[{news.get('source', '-')}] スコア:{score:+d}\n"
        report += f"  分類: {news.get('category_name', '-')}"
        if news.get("sub_category"):
            report += f" ({news['sub_category']})"
        report += f"\n  判定理由: {reason}\n"
        report += f"  内容: {news.get('text', '')[:100]}...\n"
    
    return report


def _generate_scenarios(total_score: float, gap: float, alerts: List, zero_count: int, news_count: int) -> List[str]:
    """シナリオを生成（2-3つ）"""
    scenarios = []
    
    # 評価保留が多い場合
    if news_count > 0 and zero_count / news_count > 0.5:
        scenarios.append("明確な方向性が出るまでレンジ推移となる可能性")
        scenarios.append("新たな材料をきっかけに方向感が出る可能性")
    # ベースシナリオ
    elif total_score >= 3:
        scenarios.append("好材料が継続し、短期的に堅調な展開が続く可能性")
        scenarios.append("利益確定売りが出やすく、調整を挟む可能性")
    elif total_score <= -3:
        scenarios.append("悪材料が一巡し、反発の動きが出る可能性")
        scenarios.append("追加の悪材料で下値を試す展開となる可能性")
    else:
        scenarios.append("材料待ちでレンジ推移となる可能性")
        scenarios.append("新たな材料をきっかけに方向感が出る可能性")
    
    # 乖離シナリオ
    if abs(gap) >= 3:
        if gap > 0:
            scenarios.append("海外市場の改善を受け、国内が追随して上昇する可能性")
        else:
            scenarios.append("海外市場の悪化を織り込み、国内が調整する可能性")
    
    return scenarios[:3]  # 最大3つ
