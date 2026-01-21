# Market Observer - 投資市場観測・助言ツール

## 概要

市場ニュースを自動取得・分析し、投資インパクトスコアを算出する観測ツールです。

**重要**: このツールは投資判断を行いません。

- ❌ 売買指示
- ❌ 銘柄・数量の提案
- ❌ 断定的な将来予測
- ✅ 情報収集・構造化
- ✅ 定量評価・変化検知
- ✅ 判断材料の提示

## セットアップ

### 1. 依存パッケージインストール

```bash
pip install -r requirements.txt
```

### 2. APIキー設定

[NewsAPI.org](https://newsapi.org/) でAPIキーを取得し、環境変数に設定：

```bash
# Windows
set NEWSAPI_KEY=your_api_key_here

# Linux/Mac
export NEWSAPI_KEY=your_api_key_here
```

または `.env` ファイルを作成：

```
NEWSAPI_KEY=your_api_key_here
```

## 使い方

```bash
python main.py
```

完全自動でニュース取得→分析→レポート生成が実行されます。

## 構成

```
market-observer/
├── main.py              # メインエントリポイント（完全自動実行）
├── config.py            # 設定
├── models/
│   └── news_dto.py      # ニュースDTO定義
├── fetcher/
│   └── newsapi_client.py # NewsAPIクライアント
├── analyzer/
│   ├── classifier.py    # ニュース分類
│   └── scorer.py        # インパクトスコア算出
├── alert/
│   └── detector.py      # アラート判定
├── report/
│   └── generator.py     # レポート生成
└── data/logs/           # ログ保存
```

## 投資インパクトスコア

- 範囲: **-10 〜 +10（整数）**
- 評価軸:
  1. 株価への方向性（ポジティブ/ネガティブキーワード）
  2. 影響の強度（短期/中期/構造）
  3. 影響範囲（個別/業界/市場）

### スコア解釈

| スコア | 解釈 |
|-------|------|
| +5〜+10 | ポジティブ材料が優勢 |
| +2〜+4 | やや好材料が多い |
| -1〜+1 | 平常レンジ（材料混在） |
| -4〜-2 | やや悪材料が多い |
| -10〜-5 | ネガティブ材料が優勢 |

## アラート条件

1. **前日比変化**: ±3以上のスコア変化
2. **移動平均反転**: 3日MAの符号反転
3. **国内外乖離**: スコア差±5以上

## ライセンス

MIT License
