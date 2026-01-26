"""
マーケット概況テキスト生成モジュール

マーケットデータを人間が読みやすいテキストに変換
"""
from typing import Dict, Any, List


def generate_market_summary(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """マーケット概況のテキスト要約を生成"""
    
    summary = {
        "sections": [],
        "one_liner": "",
    }
    
    # 【為替動向】
    fx_section = _generate_fx_summary(market_data.get("fx", []))
    if fx_section:
        summary["sections"].append(fx_section)
    
    # 【金利・債券】
    bond_section = _generate_bond_summary(
        market_data.get("bonds", []),
        market_data.get("interest_rate_diff"),
        market_data.get("yield_spread")
    )
    if bond_section:
        summary["sections"].append(bond_section)
    
    # 【リスク指標】
    risk_section = _generate_risk_summary(market_data.get("risk", []))
    if risk_section:
        summary["sections"].append(risk_section)
    
    # 【コモディティ】
    commodity_section = _generate_commodity_summary(market_data.get("commodity", []))
    if commodity_section:
        summary["sections"].append(commodity_section)
    
    # 【株式市場】
    index_section = _generate_index_summary(market_data.get("index", []))
    if index_section:
        summary["sections"].append(index_section)
    
    # 一言まとめ
    summary["one_liner"] = _generate_one_liner(market_data)
    
    return summary


def _generate_fx_summary(fx_data: List[Dict]) -> Dict[str, Any]:
    """為替セクションの要約を生成"""
    if not fx_data:
        return None
    
    lines = []
    usdjpy = next((f for f in fx_data if f["symbol"] == "USDJPY=X"), None)
    eurjpy = next((f for f in fx_data if f["symbol"] == "EURJPY=X"), None)
    
    if usdjpy:
        direction = "円安" if usdjpy["change"] > 0 else ("円高" if usdjpy["change"] < 0 else "横ばい")
        lines.append(
            f"ドル円は{usdjpy['price']:.2f}円で取引中。"
            f"前日比{usdjpy['change']:+.2f}円（{usdjpy['change_percent']:+.2f}%）と{direction}方向。"
        )
        if usdjpy.get("weekly_change"):
            weekly_dir = "上昇" if usdjpy["weekly_change"] > 0 else "下落"
            lines.append(
                f"週間では{usdjpy['weekly_change']:+.2f}円（{usdjpy['weekly_change_percent']:+.2f}%）の{weekly_dir}。"
            )
    
    if eurjpy:
        lines.append(f"ユーロ円は{eurjpy['price']:.2f}円で推移。")
    
    # 解説
    if usdjpy:
        if usdjpy["change"] > 0.3:
            lines.append("→ 円安基調が継続。日米金利差拡大が背景か。")
        elif usdjpy["change"] < -0.3:
            lines.append("→ 円高方向に振れる。リスクオフの動きか。")
        else:
            lines.append("→ 小動きで方向感に欠ける展開。")
    
    return {
        "title": "為替動向",
        "icon": "💱",
        "content": "\n".join(lines)
    }


def _generate_bond_summary(bonds: List[Dict], rate_diff: Dict, yield_spread: Dict) -> Dict[str, Any]:
    """金利・債券セクションの要約を生成"""
    if not bonds:
        return None
    
    lines = []
    us10y = next((b for b in bonds if b["symbol"] == "^TNX"), None)
    us5y = next((b for b in bonds if b["symbol"] == "^FVX"), None)
    
    if us10y:
        lines.append(
            f"米国債10年利回りは{us10y['price']:.3f}%（前日比{us10y['change']:+.3f}）。"
        )
        if us10y.get("weekly_change"):
            lines.append(f"週間で{us10y['weekly_change']:+.3f}%の変動。")
    
    # 日米金利差
    if rate_diff:
        lines.append(
            f"日米金利差（10年）は約{rate_diff['diff']:.1f}%。"
            f"（米{rate_diff['us10y']:.2f}% - 日{rate_diff['jp10y']:.2f}%）"
        )
        if rate_diff['diff'] > 3.0:
            lines.append("金利差拡大で円売り圧力継続。")
    
    # 逆イールド
    if yield_spread:
        spread = yield_spread.get("spread_5_10", 0)
        if spread < 0:
            lines.append(f"5-10年スプレッドは{spread:.2f}%で逆イールド状態。景気後退懸念を示唆。")
        else:
            lines.append(f"5-10年スプレッドは{spread:.2f}%で正常なイールドカーブ。")
    
    # 解説
    if us10y:
        if us10y["change"] > 0.03:
            lines.append("→ 金利上昇でグロース株に逆風。")
        elif us10y["change"] < -0.03:
            lines.append("→ 金利低下でリスク資産に追い風。")
    
    return {
        "title": "金利・債券",
        "icon": "📊",
        "content": "\n".join(lines)
    }


def _generate_risk_summary(risk_data: List[Dict]) -> Dict[str, Any]:
    """リスク指標セクションの要約を生成"""
    if not risk_data:
        return None
    
    lines = []
    vix = next((r for r in risk_data if r["symbol"] == "^VIX"), None)
    
    if vix:
        lines.append(f"VIX指数: {vix['price']:.1f}（前日比{vix['change']:+.1f}）")
        
        # VIXレベルの解説
        if vix['price'] < 15:
            lines.append("→ 15以下で非常に落ち着いた相場。楽観モード。")
        elif vix['price'] < 20:
            lines.append("→ 20以下で市場は安定。リスクオン継続。")
        elif vix['price'] < 30:
            lines.append("→ 20-30で警戒感高まる。ボラティリティ上昇。")
        else:
            lines.append("→ 30超えで恐怖モード。リスク回避が加速。")
    
    return {
        "title": "リスク指標",
        "icon": "⚠️",
        "content": "\n".join(lines)
    }


def _generate_commodity_summary(commodities: List[Dict]) -> Dict[str, Any]:
    """コモディティセクションの要約を生成"""
    if not commodities:
        return None
    
    lines = []
    gold = next((c for c in commodities if c["symbol"] == "GC=F"), None)
    oil = next((c for c in commodities if c["symbol"] == "CL=F"), None)
    
    if gold:
        lines.append(f"ゴールド: ${gold['price']:.2f}（前日比${gold['change']:+.2f}）")
        lines.append(f"  {gold.get('description', '')}")
    
    if oil:
        lines.append(f"原油WTI: ${oil['price']:.2f}（前日比${oil['change']:+.2f}）")
        lines.append(f"  {oil.get('description', '')}")
    
    return {
        "title": "コモディティ",
        "icon": "🛢️",
        "content": "\n".join(lines)
    }


def _generate_index_summary(indices: List[Dict]) -> Dict[str, Any]:
    """株式指数セクションの要約を生成"""
    if not indices:
        return None
    
    lines = []
    sp500 = next((i for i in indices if i["symbol"] == "^GSPC"), None)
    nikkei = next((i for i in indices if i["symbol"] == "^N225"), None)
    
    if sp500:
        direction = "上昇" if sp500["change"] > 0 else ("下落" if sp500["change"] < 0 else "横ばい")
        lines.append(
            f"S&P500: {sp500['price']:,.2f}（{sp500['change']:+.2f}, {sp500['change_percent']:+.2f}%）"
        )
        if sp500.get("weekly_change_percent"):
            lines.append(f"  週間: {sp500['weekly_change_percent']:+.2f}%")
    
    if nikkei:
        lines.append(
            f"日経平均: {nikkei['price']:,.2f}（{nikkei['change']:+.2f}, {nikkei['change_percent']:+.2f}%）"
        )
        if nikkei.get("weekly_change_percent"):
            lines.append(f"  週間: {nikkei['weekly_change_percent']:+.2f}%")
    
    return {
        "title": "株式市場",
        "icon": "📈",
        "content": "\n".join(lines)
    }


def _generate_one_liner(market_data: Dict[str, Any]) -> str:
    """一言まとめを生成"""
    fx = market_data.get("fx", [])
    risk = market_data.get("risk", [])
    
    usdjpy = next((f for f in fx if f["symbol"] == "USDJPY=X"), None)
    vix = next((r for r in risk if r["symbol"] == "^VIX"), None)
    
    # トレンド判定
    fx_trend = ""
    if usdjpy:
        if usdjpy["change"] > 0.2:
            fx_trend = "円安"
        elif usdjpy["change"] < -0.2:
            fx_trend = "円高"
        else:
            fx_trend = "小動き"
    
    risk_trend = ""
    if vix:
        if vix["price"] < 20:
            risk_trend = "リスクオン"
        elif vix["price"] < 30:
            risk_trend = "警戒モード"
        else:
            risk_trend = "リスクオフ"
    
    # 組み合わせ
    if fx_trend and risk_trend:
        summary = f"{fx_trend}・{risk_trend}モード"
    elif fx_trend:
        summary = f"{fx_trend}モード"
    else:
        summary = "様子見モード"
    
    # 詳細
    details = []
    if usdjpy:
        details.append(f"ドル円{usdjpy['price']:.0f}円台")
    if vix:
        details.append(f"VIX {vix['price']:.0f}")
    
    return f"💬 {summary}：{', '.join(details)}"
