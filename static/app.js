/* Market Observer Dashboard - Professional Layout JavaScript */

// DOM読み込み完了後に実行
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setupTabs();
});

// 更新ボタンクリック時
async function refreshData() {
    const btn = document.getElementById('refresh-btn');
    btn.disabled = true;
    btn.textContent = '⏳ 更新中...';

    await loadData();

    btn.disabled = false;
    btn.textContent = '🔄 更新';
}

// データ取得
async function loadData() {
    const loading = document.getElementById('loading');
    const mainContent = document.getElementById('main-content');
    const error = document.getElementById('error');

    loading.classList.remove('hidden');
    mainContent.classList.add('hidden');
    error.classList.add('hidden');

    try {
        const response = await fetch('/api/report');
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'データ取得に失敗しました');
        }

        renderDashboard(data);

        loading.classList.add('hidden');
        mainContent.classList.remove('hidden');

    } catch (err) {
        loading.classList.add('hidden');
        error.classList.remove('hidden');
        document.getElementById('error-message').textContent = err.message;
    }
}

// ダッシュボード描画
function renderDashboard(data) {
    // ヒーローセクション
    renderHeroSection(data);

    // サブパネル（7日比較・観測メモ）
    renderSubPanels(data);

    // マーケットデータ（為替・国債利回り）
    if (data.market_data) {
        // マーケット概況テキスト
        if (data.market_data.summary) {
            renderMarketSummaryText(data.market_data.summary);
        }
        renderMarketQuotes(data.market_data);
    }

    // 経済指標
    if (data.economic_indicators) {
        renderEconomicIndicators(data.economic_indicators);
    }

    // 優先度カード
    renderPriorityCard('priority-fed', data.priority_macro.fed);
    renderPriorityCard('priority-treasury', data.priority_macro.treasury);
    renderPriorityCard('priority-usdjpy', data.priority_macro.usdjpy);
    renderPriorityCard('priority-employment', data.priority_macro.employment);
    renderPriorityCard('priority-inflation', data.priority_macro.inflation);
    renderPriorityCard('priority-ism', data.priority_macro.ism);

    // 判断しやすさ
    const judgementText = data.has_priority
        ? '判断材料が出ている日です。上記の情報を確認してください。'
        : '判断の土台となる情報が少ない日です。様子見が妥当かもしれません。';
    document.querySelector('#judgement-summary .judgement-text').textContent = '📍 ' + judgementText;

    // ニュースタブ（統合版）
    renderHighlightNewsTab(data.news);
    renderNews('positive-news', data.news.positive, 'positive');
    renderNews('negative-news', data.news.negative, 'negative');
    renderNews('neutral-news', data.news.neutral, 'neutral');
    renderPoliticalNewsTab(data.political_events);
}

// サブパネル描画（7日比較・観測メモ）
function renderSubPanels(data) {
    // 7日比較
    const historyEl = document.getElementById('history-mini');
    if (historyEl) {
        if (data.history && data.history.has_history &&
            typeof data.history.score_change === 'number') {
            const h = data.history;
            const scoreChange = h.score_change >= 0 ? `+${h.score_change.toFixed(1)}` : h.score_change.toFixed(1);
            const zeroRatioChange = h.zero_ratio_change || 0;
            const zeroChange = zeroRatioChange >= 0 ? `+${zeroRatioChange}` : zeroRatioChange;
            historyEl.innerHTML = `
                <div class="mini-stat">スコア: <span class="${h.score_change >= 0 ? 'up' : 'down'}">${scoreChange}</span></div>
                <div class="mini-stat">評価保留: <span class="${zeroRatioChange <= 0 ? 'up' : 'down'}">${zeroChange}%</span></div>
            `;
        } else {
            historyEl.innerHTML = '<span class="no-data-mini">データなし</span>';
        }
    }

    // 観測メモ
    const triggersEl = document.getElementById('triggers-mini');
    if (triggersEl) {
        if (data.triggers && data.triggers.length > 0) {
            triggersEl.innerHTML = data.triggers.slice(0, 2).map(t =>
                `<div class="mini-trigger">${t.name}</div>`
            ).join('');
        } else {
            triggersEl.innerHTML = '<span class="no-data-mini">なし</span>';
        }
    }
}

// ヒーローセクション描画
function renderHeroSection(data) {
    // タイムスタンプ
    document.getElementById('timestamp').textContent = data.timestamp;

    // 総合スコア
    const totalScore = data.summary.total_score;
    const scoreEl = document.getElementById('total-score');
    scoreEl.textContent = (totalScore >= 0 ? '+' : '') + totalScore.toFixed(1);

    if (totalScore >= 2) {
        scoreEl.className = 'score-value positive';
    } else if (totalScore <= -2) {
        scoreEl.className = 'score-value negative';
    } else {
        scoreEl.className = 'score-value neutral';
    }

    // センチメントバッジ
    const badge = document.getElementById('sentiment-badge');
    if (totalScore >= 3) {
        badge.textContent = '強気';
        badge.className = 'sentiment-badge positive';
    } else if (totalScore >= 1) {
        badge.textContent = 'やや強気';
        badge.className = 'sentiment-badge positive';
    } else if (totalScore <= -3) {
        badge.textContent = '弱気';
        badge.className = 'sentiment-badge negative';
    } else if (totalScore <= -1) {
        badge.textContent = 'やや弱気';
        badge.className = 'sentiment-badge negative';
    } else {
        badge.textContent = '中立';
        badge.className = 'sentiment-badge neutral';
    }

    // 今日の一言
    document.querySelector('#one-liner .one-liner-text').textContent = data.one_liner;

    // 統計
    document.getElementById('news-count').textContent = data.summary.news_count + '件';
    document.getElementById('domestic-foreign').textContent =
        `${data.summary.domestic_score >= 0 ? '+' : ''}${data.summary.domestic_score.toFixed(1)} / ${data.summary.foreign_score >= 0 ? '+' : ''}${data.summary.foreign_score.toFixed(1)}`;
    document.getElementById('zero-ratio').textContent = data.summary.zero_ratio + '%';
}

// 優先度カード描画
function renderPriorityCard(id, item) {
    const el = document.getElementById(id);
    const statusEl = el.querySelector('.card-status');
    const summaryEl = el.querySelector('.card-summary');
    const articlesEl = el.querySelector('.card-articles');

    if (item.has) {
        el.classList.add('has');
        const avgScore = item.avg_score || 0;
        statusEl.innerHTML = `${item.count}件 <span style="color: ${avgScore > 0 ? 'var(--accent-green)' : (avgScore < 0 ? 'var(--accent-red)' : 'var(--text-secondary)')}">(${avgScore >= 0 ? '+' : ''}${avgScore})</span>`;

        if (item.summary) {
            summaryEl.textContent = item.summary;
        }

        if (item.articles && item.articles.length > 0) {
            articlesEl.innerHTML = item.articles.map(article => {
                const score = article.score || 0;
                const scoreClass = score > 0 ? 'positive' : (score < 0 ? 'negative' : '');
                return `<div class="card-article">
                    <span class="article-score ${scoreClass}">${score >= 0 ? '+' : ''}${score}</span>
                    <a href="${article.url || '#'}" target="_blank">${article.title || '(タイトルなし)'}</a>
                </div>`;
            }).join('');
        }
    } else {
        el.classList.remove('has');
        statusEl.textContent = '該当なし';
        summaryEl.textContent = '';
        articlesEl.innerHTML = '';
    }
}

// 注目ニュース（タブ内）描画
function renderHighlightNewsTab(news) {
    const container = document.getElementById('highlight-news');
    if (!container) return;

    // +3以上/-3以下のニュースを抽出
    const highlights = [
        ...news.positive.filter(n => Math.abs(n.impact_score) >= 3),
        ...news.negative.filter(n => Math.abs(n.impact_score) >= 3)
    ].sort((a, b) => Math.abs(b.impact_score) - Math.abs(a.impact_score)).slice(0, 10);

    if (highlights.length === 0) {
        container.innerHTML = '<p class="no-data">本日は特に注目すべきニュースはありません。</p>';
        return;
    }

    container.innerHTML = `<div class="highlight-grid">${highlights.map(n => {
        const score = n.impact_score || 0;
        const type = score > 0 ? 'positive' : 'negative';
        return `
            <div class="highlight-item ${type}">
                <div class="item-header">
                    <span class="item-source">${n.source_name || n.source || 'Unknown'}</span>
                    <span class="item-score ${type}">${score >= 0 ? '+' : ''}${score}</span>
                </div>
                <div class="item-title">
                    <a href="${n.url || '#'}" target="_blank">${n.title || (n.text || '').substring(0, 80)}</a>
                </div>
                <div class="item-reason">${n.score_reason || ''}</div>
            </div>
        `;
    }).join('')}</div>`;
}

// 政治発言（タブ内）描画
function renderPoliticalNewsTab(politicalEvents) {
    const container = document.getElementById('political-news');
    if (!container) return;

    if (!politicalEvents || politicalEvents.length === 0) {
        container.innerHTML = '<p class="no-data">本日は重要人物の発言はありません。</p>';
        return;
    }

    container.innerHTML = `<div class="political-list">${politicalEvents.map(event => `
        <div class="political-group">
            <div class="political-speaker">
                <span class="speaker-icon">👤</span>
                <span class="speaker-name">${event.speaker || '不明'}</span>
                <span class="speaker-count">(${event.count}件)</span>
            </div>
            <div class="political-articles">
                ${event.articles.map(a => `
                    <div class="political-article">
                        <a href="${a.url || '#'}" target="_blank">${a.title || '(タイトルなし)'}</a>
                        ${a.snippet ? `<p class="article-snippet">${a.snippet}</p>` : ''}
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('')}</div>`;
}

// 履歴描画
function renderHistory(history, summary) {
    const container = document.getElementById('history-content');

    const scoreDiff = summary.total_score - history.avg_total_score;
    let scoreComment = '最近1週間と比べて、大きな変化はありません。';
    if (scoreDiff > 0.5) scoreComment = '最近1週間と比べると、やや良いニュースが増えています。';
    if (scoreDiff < -0.5) scoreComment = '最近1週間と比べると、やや慎重な評価が増えています。';

    const zeroDiff = summary.zero_ratio - history.avg_zero_ratio;
    let zeroComment = 'いつもと同じくらいです。';
    if (zeroDiff > 10) zeroComment = '今日は、判断材料として使いにくいニュースが多い日です。';
    if (zeroDiff < -10) zeroComment = '今日は、判断しやすいニュースが多い日です。';

    container.innerHTML = `
        <div class="history-item">
            <span class="label">総合スコア</span>
            <div class="values">
                <div class="value-block">
                    <span>過去${history.days_count}日平均</span>
                    <span>${history.avg_total_score >= 0 ? '+' : ''}${history.avg_total_score.toFixed(2)}</span>
                </div>
                <div class="value-block">
                    <span>本日</span>
                    <span>${summary.total_score >= 0 ? '+' : ''}${summary.total_score.toFixed(1)}</span>
                </div>
            </div>
            <p class="comment">→ ${scoreComment}</p>
        </div>
        <div class="history-item">
            <span class="label">評価保留の割合</span>
            <div class="values">
                <div class="value-block">
                    <span>過去${history.days_count}日平均</span>
                    <span>${history.avg_zero_ratio.toFixed(0)}%</span>
                </div>
                <div class="value-block">
                    <span>本日</span>
                    <span>${summary.zero_ratio}%</span>
                </div>
            </div>
            <p class="comment">→ ${zeroComment}</p>
        </div>
    `;
}

// トリガー描画
function renderTriggers(triggers) {
    const container = document.getElementById('triggers-list');

    if (!triggers || triggers.length === 0) {
        container.innerHTML = '<p class="no-data">現在、特筆すべき観測メモはありません。</p>';
        return;
    }

    container.innerHTML = triggers.map(t => `
        <div class="trigger-item">
            <span class="icon">💡</span>
            <span>${t.message}</span>
        </div>
    `).join('');
}

// 政治発言描画
// 政治発言描画（詳細表示）
function renderPoliticalEvents(events) {
    const container = document.getElementById('political-list');
    const section = document.getElementById('political-section');

    if (!events || events.length === 0) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    container.innerHTML = events.map(e => `
        <div class="political-item">
            <div class="speaker">${e.speaker}</div>
            <div class="themes">
                ${e.themes.map(t => `<span class="theme-tag">${t.name}（${t.count}件）</span>`).join('')}
            </div>
            <div class="political-articles">
                ${(e.items || []).map(item => {
        const url = item.url || '#';
        const sourceName = item.source_name || '';
        const title = item.title || item.summary || 'タイトルなし';
        const description = item.description || ''
        const score = item.score || 0;
        const scoreClass = score > 0 ? 'positive' : (score < 0 ? 'negative' : 'neutral');

        return `
                    <div class="political-article">
                        <div class="article-header">
                            <span class="article-score ${scoreClass}">${score >= 0 ? '+' : ''}${score}</span>
                            <a href="${url}" target="_blank" class="article-title">${title}</a>
                        </div>
                        <p class="article-summary">${description}</p>
                        <div class="article-meta">
                            <span class="meta-source">[${sourceName}]</span>
                            <span class="meta-note">${item.summary}</span>
                        </div>
                    </div>`;
    }).join('')}
            </div>
        </div>
    `).join('');
}

// ニュース描画（詳細評価付き）
function renderNews(containerId, news, type) {
    const container = document.getElementById(containerId);

    if (!news || news.length === 0) {
        container.innerHTML = '<p class="no-data">該当するニュースはありません。</p>';
        return;
    }

    container.innerHTML = news.map(n => {
        const score = n.impact_score || 0;
        const scoreClass = score > 0 ? 'positive' : (score < 0 ? 'negative' : 'neutral');
        const star = Math.abs(score) >= 3 ? ' ★' : '';
        const url = n.url || '#';
        const title = n.title || (n.text || '').substring(0, 80);

        const confidence = n.confidence || 0;
        const confidenceStars = '★'.repeat(confidence) + '☆'.repeat(5 - confidence);
        const timeHorizon = n.time_horizon || 'medium';
        const timeLabel = { short: '短期', medium: '中期', long: '長期' }[timeHorizon] || '中期';

        const positiveFactors = (n.positive_factors || []).slice(0, 3);
        const negativeFactors = (n.negative_factors || []).slice(0, 3);
        const uncertaintyFactors = (n.uncertainty_factors || []).slice(0, 2);

        const hasFactors = positiveFactors.length > 0 || negativeFactors.length > 0 || uncertaintyFactors.length > 0;

        return `
            <div class="news-item">
                <div class="header">
                    <span class="source">${n.source_name || n.source || 'Unknown'}</span>
                    <span class="score ${scoreClass}">${score >= 0 ? '+' : ''}${score}${star}</span>
                </div>
                <div class="title">
                    <a href="${url}" target="_blank">${title}</a>
                </div>
                <div class="category">${n.category_name || ''} ${n.sub_category ? '(' + n.sub_category + ')' : ''}</div>
                <div class="evaluation-details">
                    <div class="eval-meta">
                        <span class="confidence">確信度: ${confidenceStars}</span>
                        <span class="time-horizon">時間軸: ${timeLabel}</span>
                    </div>
                    <div class="reason"><strong>判定理由:</strong> ${n.score_reason || '-'}</div>
                    ${hasFactors ? `
                    <div class="factors">
                        ${positiveFactors.length > 0 ? `<div class="factor-group positive-factors"><span class="factor-label">📈 プラス要因:</span> ${positiveFactors.join(' / ')}</div>` : ''}
                        ${negativeFactors.length > 0 ? `<div class="factor-group negative-factors"><span class="factor-label">📉 マイナス要因:</span> ${negativeFactors.join(' / ')}</div>` : ''}
                        ${uncertaintyFactors.length > 0 ? `<div class="factor-group uncertainty-factors"><span class="factor-label">⚠️ 不確実要因:</span> ${uncertaintyFactors.join(' / ')}</div>` : ''}
                    </div>
                    ` : ''}
                </div>
                <div class="text">${(n.description || n.text || '').substring(0, 150)}...</div>
            </div>
        `;
    }).join('');
}

// タブ切り替え
function setupTabs() {
    const tabs = document.querySelectorAll('.tab-btn');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const target = tab.dataset.tab;
            document.querySelectorAll('.news-tab-content').forEach(c => c.classList.add('hidden'));
            document.getElementById(target + '-news').classList.remove('hidden');
        });
    });
}

// マーケットクォート描画（為替・国債利回り）+ チャート
function renderMarketQuotes(marketData) {
    const container = document.getElementById('market-quotes');
    if (!container) return;

    // 表示するデータを構築
    const quotes = [];

    // カテゴリ定義
    const categories = [
        { key: 'fx', icon: '💱', decimals: 2, unit: '' },
        { key: 'bonds', icon: '📊', decimals: 3, unit: '%' },
        { key: 'risk', icon: '⚠️', decimals: 1, unit: '' },
        { key: 'commodity', icon: '🛢️', decimals: 2, unit: '$' },
        { key: 'index', icon: '📈', decimals: 2, unit: '' },
    ];

    // 各カテゴリのデータを統合
    categories.forEach(cat => {
        const data = marketData[cat.key];
        if (data && data.length > 0) {
            data.forEach((q, i) => {
                const priceStr = cat.unit === '$'
                    ? `$${q.price.toFixed(cat.decimals)}`
                    : cat.unit === '%'
                        ? `${q.price.toFixed(cat.decimals)}%`
                        : q.price.toLocaleString('ja-JP', { minimumFractionDigits: cat.decimals, maximumFractionDigits: cat.decimals });

                quotes.push({
                    id: `chart-${cat.key}-${i}`,
                    name: q.name,
                    price: priceStr,
                    change: q.change,
                    change_percent: q.change_percent,
                    direction: q.direction,
                    category: cat.key,
                    icon: cat.icon,
                    decimals: cat.decimals,
                    history: q.history || []
                });
            });
        }
    });

    if (quotes.length === 0) {
        container.innerHTML = '<p class="no-data">マーケットデータを取得中...</p>';
        return;
    }

    // カードを生成（canvas含む）
    container.innerHTML = quotes.map(q => {
        const changeSign = q.change >= 0 ? '+' : '';
        const changePercentSign = q.change_percent >= 0 ? '+' : '';
        const directionClass = q.direction || (q.change > 0 ? 'up' : (q.change < 0 ? 'down' : 'flat'));

        // トレンド矢印
        let trendArrow = '→';
        if (q.change > 0) trendArrow = '↑';
        else if (q.change < 0) trendArrow = '↓';

        return `
            <div class="market-card">
                <div class="market-card-header">
                    <span class="market-icon">${q.icon}</span>
                    <span class="market-name">${q.name}</span>
                </div>
                <div class="market-card-chart">
                    <canvas id="${q.id}" width="200" height="80"></canvas>
                </div>
                <div class="market-card-body">
                    <div class="market-price-row">
                        <span class="market-price">${q.price}</span>
                        <span class="trend-arrow ${directionClass}">${trendArrow}</span>
                    </div>
                    <div class="market-change ${directionClass}">
                        ${changeSign}${Math.abs(q.change).toFixed(q.decimals)} (${changePercentSign}${q.change_percent.toFixed(2)}%)
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // Chart.jsでチャートを描画
    quotes.forEach(q => {
        if (q.history && q.history.length > 0) {
            renderMiniChart(q.id, q.history, q.direction);
        }
    });
}

// ミニチャート描画（Chart.js）
function renderMiniChart(canvasId, history, direction) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = history.map(d => d.date);
    const data = history.map(d => d.close);

    // 色設定（上昇=緑、下落=赤、横ばい=青）
    const lineColor = direction === 'up' ? '#00d084' : (direction === 'down' ? '#ff4757' : '#1da1f2');
    const bgColor = direction === 'up' ? 'rgba(0, 208, 132, 0.1)' : (direction === 'down' ? 'rgba(255, 71, 87, 0.1)' : 'rgba(29, 161, 242, 0.1)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                borderColor: lineColor,
                backgroundColor: bgColor,
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 3,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                x: {
                    display: false,
                },
                y: {
                    display: false,
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// 経済指標描画
function renderEconomicIndicators(indicators) {
    const container = document.getElementById('economic-indicators');
    if (!container) return;

    if (!indicators || indicators.length === 0) {
        container.innerHTML = '<p class="no-data">現在、重要な経済指標の発表はありません。</p>';
        return;
    }

    container.innerHTML = indicators.map(ind => {
        const impactLabel = { high: '重要', medium: '中', low: '低' }[ind.impact] || '';

        // サプライズ判定
        let surpriseText = '';
        let surpriseClass = ind.surprise_direction || 'pending';
        if (ind.surprise !== null && ind.surprise !== undefined) {
            if (ind.surprise_direction === 'positive_strong') surpriseText = `予想を大幅上振れ (+${ind.surprise}%)`;
            else if (ind.surprise_direction === 'positive') surpriseText = `予想上振れ (+${ind.surprise}%)`;
            else if (ind.surprise_direction === 'negative_strong') surpriseText = `予想を大幅下振れ (${ind.surprise}%)`;
            else if (ind.surprise_direction === 'negative') surpriseText = `予想下振れ (${ind.surprise}%)`;
            else if (ind.surprise_direction === 'inline') surpriseText = '予想通り';
        } else {
            surpriseText = '結果待ち';
        }

        return `
            <div class="economic-card">
                <div class="ec-header">
                    <span class="ec-name">${ind.name}</span>
                    <span class="ec-impact ${ind.impact}">${impactLabel}</span>
                </div>
                <div class="ec-values">
                    <div class="ec-value-item">
                        <span class="ec-value-label">予想</span>
                        <span class="ec-value-num">${ind.forecast || '-'}</span>
                    </div>
                    <div class="ec-value-item">
                        <span class="ec-value-label">結果</span>
                        <span class="ec-value-num actual">${ind.actual || '-'}</span>
                    </div>
                    <div class="ec-value-item">
                        <span class="ec-value-label">前回</span>
                        <span class="ec-value-num">${ind.previous || '-'}</span>
                    </div>
                </div>
                <div class="ec-surprise ${surpriseClass}">${surpriseText}</div>
            </div>
        `;
    }).join('');
}

// マーケット概況テキスト描画
function renderMarketSummaryText(summary) {
    // 一言まとめ
    const oneLinerEl = document.getElementById('market-one-liner');
    if (oneLinerEl && summary.one_liner) {
        oneLinerEl.innerHTML = `<div class="one-liner-content">${summary.one_liner}</div>`;
    }

    // 各セクションのテキスト
    const summaryEl = document.getElementById('market-summary-text');
    if (!summaryEl || !summary.sections) return;

    summaryEl.innerHTML = summary.sections.map(section => {
        // テキスト内の改行をbrに変換
        const contentHtml = section.content
            .split('\n')
            .map(line => {
                // 矢印で始まる行（解説）は強調
                if (line.startsWith('→')) {
                    return `<span class="summary-insight">${line}</span>`;
                }
                // 2スペースインデントは小さめに
                if (line.startsWith('  ')) {
                    return `<span class="summary-sub">${line.trim()}</span>`;
                }
                return `<span class="summary-line">${line}</span>`;
            })
            .join('');

        return `
            <div class="market-summary-section">
                <div class="summary-section-header">
                    <span class="summary-icon">${section.icon}</span>
                    <span class="summary-title">${section.title}</span>
                </div>
                <div class="summary-section-content">${contentHtml}</div>
            </div>
        `;
    }).join('');
}
