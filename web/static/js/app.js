/* AI Legal Document Analyzer — Frontend */

const UI = {
    uploadArea:     document.getElementById('uploadArea'),
    fileInput:      document.getElementById('fileInput'),
    ingestBtn:      document.getElementById('ingestBtn'),
    uploadStatus:   document.getElementById('uploadStatus'),
    queryInput:     document.getElementById('queryInput'),
    analyzeBtn:     document.getElementById('analyzeBtn'),
    resultsSection: document.getElementById('resultsSection'),
    riskSummary:    document.getElementById('riskSummary'),
    resultsContent: document.getElementById('resultsContent'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText:    document.getElementById('loadingText'),
};

let selectedFile = null;

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    // File selection
    UI.uploadArea.addEventListener('click', () => UI.fileInput.click());
    UI.fileInput.addEventListener('change', e => handleFileSelection(e.target.files[0]));

    // Drag & Drop
    UI.uploadArea.addEventListener('dragover', e => {
        e.preventDefault();
        UI.uploadArea.classList.add('drag-over');
    });
    UI.uploadArea.addEventListener('dragleave', () => UI.uploadArea.classList.remove('drag-over'));
    UI.uploadArea.addEventListener('drop', e => {
        e.preventDefault();
        UI.uploadArea.classList.remove('drag-over');
        handleFileSelection(e.dataTransfer.files[0]);
    });

    // Buttons
    UI.ingestBtn.addEventListener('click', handleIngestion);
    UI.analyzeBtn.addEventListener('click', handleAnalysis);

    // Quick query chips
    document.querySelectorAll('.btn-quick-query').forEach(btn => {
        btn.addEventListener('click', () => {
            UI.queryInput.value = btn.dataset.query;
            UI.queryInput.focus();
        });
    });

    // Allow Ctrl+Enter / Cmd+Enter to trigger analysis
    UI.queryInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            handleAnalysis();
        }
    });
}

function handleFileSelection(file) {
    if (!file) return;
    selectedFile = file;

    const iconHtml = `<svg style="width:18px;height:18px;vertical-align:middle;margin-right:6px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`;
    UI.uploadArea.querySelector('.upload-text').innerHTML =
        `${iconHtml}<strong>${file.name}</strong> selected (${formatBytes(file.size)})`;

    UI.ingestBtn.disabled = false;
    clearStatus(UI.uploadStatus);
}

async function handleIngestion() {
    if (!selectedFile) return;

    setLoading(true, 'Ingesting document…');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch('/api/ingest', { method: 'POST', body: formData });
        const data = await safeJson(response);

        if (response.ok && data.status === 'success') {
            showStatus(UI.uploadStatus, 'success',
                `✅ Done! Processed ${data.num_clauses} clauses from "${data.filename}". Ready to analyze.`);
        } else {
            showStatus(UI.uploadStatus, 'error', `❌ ${data.detail || data.error || 'Ingestion failed.'}`);
        }
    } catch (err) {
        showStatus(UI.uploadStatus, 'error', `❌ Network error: ${err.message}`);
    } finally {
        setLoading(false);
    }
}

async function handleAnalysis() {
    const query = UI.queryInput.value.trim();
    if (!query) {
        UI.queryInput.focus();
        return;
    }

    setLoading(true, 'Analyzing document…');
    UI.resultsSection.style.display = 'none';
    UI.riskSummary.style.display = 'none';

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const data = await safeJson(response);

        if (response.ok) {
            renderResults(data);
        } else {
            UI.resultsContent.textContent = data.detail || data.error || 'Analysis failed.';
            UI.resultsSection.style.display = 'block';
        }
    } catch (err) {
        UI.resultsContent.textContent = `Network error: ${err.message}`;
        UI.resultsSection.style.display = 'block';
    } finally {
        setLoading(false);
        UI.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function renderResults(data) {
    // Risk summary badges
    const report = data.overall_report || {};
    if (report.overall_risk_score !== undefined) {
        UI.riskSummary.innerHTML = `
            <span class="risk-badge risk-score-badge">📊 Score: ${report.overall_risk_score}/10</span>
            <span class="risk-badge risk-high">🔴 High: ${report.high_risk_count || 0}</span>
            <span class="risk-badge risk-medium">🟡 Medium: ${report.medium_risk_count || 0}</span>
            <span class="risk-badge risk-low">🟢 Low: ${report.low_risk_count || 0}</span>
            <span class="risk-badge" style="background:rgba(148,163,184,0.1);border:1px solid #475569;color:#94a3b8">
                📑 Clauses analyzed: ${data.num_clauses_analyzed || 0}
            </span>
        `;
        UI.riskSummary.style.display = 'flex';
    }

    // Format answer text
    UI.resultsContent.innerHTML = formatAnswer(data.answer || 'No answer generated.');
    UI.resultsSection.style.display = 'block';
}

function formatAnswer(text) {
    // Bold **text**
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic *text*
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Simple newlines → <br>
    text = text.replace(/\n/g, '<br>');
    return text;
}

/* ---- Helpers ---- */

async function safeJson(response) {
    const ct = response.headers.get('content-type') || '';
    if (ct.includes('application/json')) return response.json();
    const text = await response.text();
    return { error: text || response.statusText };
}

function setLoading(active, message = 'Processing…') {
    UI.loadingText.textContent = message;
    UI.loadingOverlay.classList.toggle('active', active);
}

function showStatus(el, type, message) {
    el.className = `status-message ${type}`;
    el.textContent = message;
}

function clearStatus(el) {
    el.className = 'status-message';
    el.textContent = '';
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}
