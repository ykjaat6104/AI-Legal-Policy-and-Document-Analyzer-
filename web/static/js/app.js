
const UI = {
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    ingestBtn: document.getElementById('ingestBtn'),
    uploadStatus: document.getElementById('uploadStatus'),
    queryInput: document.getElementById('queryInput'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    resultsSection: document.getElementById('resultsSection'),
    resultsContent: document.getElementById('resultsContent'),
    loadingOverlay: document.getElementById('loadingOverlay'),
};

let selectedFile = null;

// init events
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    // upload triggers
    UI.uploadArea.addEventListener('click', () => UI.fileInput.click());
    UI.fileInput.addEventListener('change', (e) => handleFileSelection(e.target.files[0]));

    // drag and drop
    UI.uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        UI.uploadArea.classList.add('drag-over');
    });

    UI.uploadArea.addEventListener('dragleave', () => UI.uploadArea.classList.remove('drag-over'));

    UI.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        UI.uploadArea.classList.remove('drag-over');
        handleFileSelection(e.dataTransfer.files[0]);
    });

    // buttons
    UI.ingestBtn.addEventListener('click', handleIngestion);
    UI.analyzeBtn.addEventListener('click', handleAnalysis);

    // quick queries
    document.querySelectorAll('.btn-quick-query').forEach(btn => {
        btn.addEventListener('click', () => {
            UI.queryInput.value = btn.dataset.query;
            UI.queryInput.focus();
        });
    });
}

function handleFileSelection(file) {
    if (!file) return;
    selectedFile = file;
    UI.uploadArea.querySelector('.upload-text').innerHTML = `<strong>${file.name}</strong> selected`;
    UI.ingestBtn.disabled = false;
    UI.uploadStatus.textContent = '';
}

async function handleIngestion() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    setLoading(true);

    try {
        const response = await fetch('/api/ingest', {
            method: 'POST',
            body: formData
        });

        const data = await parseResponse(response);

        if (response.ok) {
            UI.uploadStatus.className = 'status-message success';
            UI.uploadStatus.textContent = `done: processed ${data.num_clauses} clauses`;
        } else {
            showError(UI.uploadStatus, data.detail || data.error || 'failed');
        }
    } catch (error) {
        showError(UI.uploadStatus, error.message);
    } finally {
        setLoading(false);
    }
}

async function handleAnalysis() {
    const query = UI.queryInput.value.trim();
    if (!query) return;

    setLoading(true);
    UI.resultsSection.style.display = 'none';

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await parseResponse(response);

        if (response.ok) {
            renderAnalysis(data.answer);
        } else {
            UI.resultsContent.textContent = data.detail || data.error || 'failed';
            UI.resultsSection.style.display = 'block';
        }
    } catch (error) {
        UI.resultsContent.textContent = error.message;
        UI.resultsSection.style.display = 'block';
    } finally {
        setLoading(false);
    }
}

async function parseResponse(response) {
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
        return await response.json();
    }
    const text = await response.text();
    return { error: text || response.statusText };
}

function renderAnalysis(answer) {
    UI.resultsContent.innerHTML = formatLegalText(answer);
    UI.resultsSection.style.display = 'block';
    UI.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function formatLegalText(text) {
    let formatted = text;
    // highlight high risk
    formatted = formatted.replace(/⚠️ HIGH RISK ALERT:/g, '<div style="margin: 1rem 0; border-left: 4px solid red; padding-left: 10px;"><strong>HIGH RISK ALERT:</strong></div>');
    // format clauses
    formatted = formatted.replace(/- Clause ([^:]+):/g, '<div style="margin-top: 15px;"><strong>CLAUSE $1</strong><br>');
    // format recommendation
    formatted = formatted.replace(/Recommendation: (.+)/g, '<div style="color: #666; margin-top: 5px;">Recommendation: $1</div></div>');
    return formatted;
}

function setLoading(isActive) {
    UI.loadingOverlay.classList.toggle('active', isActive);
}

function showError(element, message) {
    element.className = 'status-message error';
    element.textContent = `error: ${message}`;
}
