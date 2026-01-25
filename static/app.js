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

    // 注目ニュース
    renderHighlightNews(data.news);

    // 履歴
    if (data.history) {
        renderHistory(data.history, data.summary);
    }

    // トリガー
    renderTriggers(data.triggers);

    // 政治発言
    renderPoliticalEvents(data.political_events);

    // ニュース一覧
    renderNews('positive-news', data.news.positive, 'positive');
    renderNews('negative-news', data.news.negative, 'negative');
    renderNews('neutral-news', data.news.neutral, 'neutral');
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

// 注目ニュース（高スコア）描画
function renderHighlightNews(news) {
    const container = document.getElementById('highlight-grid');
    const section = document.getElementById('highlight-section');

    // +3以上/-3以下のニュースを抽出
    const highlights = [
        ...news.positive.filter(n => Math.abs(n.impact_score) >= 3),
        ...news.negative.filter(n => Math.abs(n.impact_score) >= 3)
    ].sort((a, b) => Math.abs(b.impact_score) - Math.abs(a.impact_score)).slice(0, 6);

    if (highlights.length === 0) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    container.innerHTML = highlights.map(n => {
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
    }).join('');
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
