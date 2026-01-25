/* Market Observer Dashboard - JavaScript */

// DOM読み込み完了後に実行
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setupTabs();
});

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
    // タイムスタンプ
    document.getElementById('timestamp').textContent = `更新: ${data.timestamp}`;

    // サマリー
    const totalScore = data.summary.total_score;
    const scoreCard = document.getElementById('total-score-card');
    const scoreEl = document.getElementById('total-score');

    scoreEl.textContent = (totalScore >= 0 ? '+' : '') + totalScore.toFixed(1);

    if (totalScore >= 2) {
        scoreCard.className = 'summary-card score-card positive';
    } else if (totalScore <= -2) {
        scoreCard.className = 'summary-card score-card negative';
    } else {
        scoreCard.className = 'summary-card score-card neutral';
    }

    document.getElementById('domestic-foreign').textContent =
        `${data.summary.domestic_score >= 0 ? '+' : ''}${data.summary.domestic_score.toFixed(1)} / ${data.summary.foreign_score >= 0 ? '+' : ''}${data.summary.foreign_score.toFixed(1)}`;
    document.getElementById('news-count').textContent = data.summary.news_count + '件';
    document.getElementById('zero-ratio').textContent = data.summary.zero_ratio + '%';

    // 今日の一言まとめ
    document.querySelector('.one-liner .text').textContent = data.one_liner;

    // 優先度マクロ
    renderPriorityItem('priority-fed', data.priority_macro.fed);
    renderPriorityItem('priority-treasury', data.priority_macro.treasury);
    renderPriorityItem('priority-usdjpy', data.priority_macro.usdjpy);
    renderPriorityItem('priority-employment', data.priority_macro.employment);
    renderPriorityItem('priority-inflation', data.priority_macro.inflation);
    renderPriorityItem('priority-ism', data.priority_macro.ism);

    // 判断しやすさ
    const judgementText = data.has_priority
        ? '判断材料が出ている日です。上記の情報を確認してください。'
        : '判断の土台となる情報が少ない日です。様子見が妥当かもしれません。';
    document.querySelector('#judgement-summary .text').textContent = '判断のしやすさ: ' + judgementText;

    // 履歴
    if (data.history) {
        renderHistory(data.history, data.summary);
    } else {
        document.getElementById('history-section').classList.add('hidden');
    }

    // トリガー
    renderTriggers(data.triggers);

    // 評価保留理由
    renderZeroReasons(data.zero_reasons);

    // 政治発言
    renderPoliticalEvents(data.political_events);

    // ニュース
    renderNews('positive-news', data.news.positive, 'positive');
    renderNews('negative-news', data.news.negative, 'negative');
    renderNews('neutral-news', data.news.neutral, 'neutral');
}

// 優先度アイテム描画
function renderPriorityItem(id, item) {
    const el = document.getElementById(id);

    // 既存の記事リストを削除
    const existingList = el.querySelector('.priority-articles');
    if (existingList) {
        existingList.remove();
    }

    if (item.has) {
        el.classList.add('has');
        el.querySelector('.status').textContent = item.count + '件あり';

        // 記事リストを追加
        if (item.articles && item.articles.length > 0) {
            const articleList = document.createElement('div');
            articleList.className = 'priority-articles';
            articleList.innerHTML = item.articles.map(article => {
                const url = article.url || '#';
                const title = article.title || '(タイトルなし)';
                const source = article.source_name || '';
                return `<div class="priority-article">
                    <a href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>
                    <span class="article-source">${source}</span>
                </div>`;
            }).join('');
            el.appendChild(articleList);
        }
    } else {
        el.classList.remove('has');
        el.querySelector('.status').textContent = '該当なし';
    }
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

// 評価保留理由描画
function renderZeroReasons(reasons) {
    const container = document.getElementById('zero-reasons-list');

    if (!reasons || Object.keys(reasons).length === 0) {
        container.innerHTML = '<p class="no-data">評価保留ニュースはありません。</p>';
        return;
    }

    // ソート（件数順）
    const sorted = Object.entries(reasons).sort((a, b) => b[1].count - a[1].count);

    container.innerHTML = sorted.map(([reason, data]) => `
        <div class="zero-reason-item">
            <div class="reason-header">
                <span class="reason">${reason}</span>
                <span class="count">${data.count}件</span>
            </div>
            <div class="reason-articles">
                ${data.articles.map(article => {
        const url = article.url || '#';
        const title = article.title || '(タイトルなし)';
        const source = article.source_name || '';
        return `<div class="reason-article">
                        <a href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>
                        <span class="article-source">${source}</span>
                    </div>`;
    }).join('')}
            </div>
        </div>
    `).join('');
}

// 政治発言描画
function renderPoliticalEvents(events) {
    const container = document.getElementById('political-list');

    if (!events || events.length === 0) {
        container.innerHTML = '<p class="no-data">本日は該当する発言はありません。</p>';
        return;
    }

    container.innerHTML = events.map(e => `
        <div class="political-item">
            <div class="speaker">${e.speaker}</div>
            <div class="themes">
                ${e.themes.map(t => `<span class="theme-tag">${t.name}（${t.count}件）</span>`).join('')}
            </div>
            <div class="summaries">
                ${(e.items || []).map(item => {
        const url = item.url || '#';
        const sourceName = item.source_name || '';
        return `<p>・${item.summary} <a href="${url}" target="_blank" rel="noopener noreferrer" class="source-link">[${sourceName}]</a></p>`;
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
        const star = Math.abs(score) >= 2 ? ' ★' : '';
        const url = n.url || '#';
        const title = n.title || (n.text || '').substring(0, 80);

        // 詳細評価情報
        const confidence = n.confidence || 0;
        const confidenceStars = '★'.repeat(confidence) + '☆'.repeat(5 - confidence);
        const timeHorizon = n.time_horizon || 'medium';
        const timeLabel = { short: '短期', medium: '中期', long: '長期' }[timeHorizon] || '中期';

        // 要因リスト
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
                    <a href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>
                </div>
                <div class="category">${n.category_name || ''} ${n.sub_category ? '(' + n.sub_category + ')' : ''}</div>
                <div class="evaluation-details">
                    <div class="eval-meta">
                        <span class="confidence" title="確信度">確信度: ${confidenceStars}</span>
                        <span class="time-horizon" title="影響の時間軸">時間軸: ${timeLabel}</span>
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
            // アクティブ状態切り替え
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // コンテンツ切り替え
            const target = tab.dataset.tab;
            document.querySelectorAll('.news-tab-content').forEach(c => c.classList.add('hidden'));
            document.getElementById(target + '-news').classList.remove('hidden');
        });
    });
}
