// Meeting Minutes Generator - Frontend JavaScript

const API_BASE = '';  // Same origin

// Form submission
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await processMeeting();
});

async function processMeeting() {
    const processBtn = document.getElementById('processBtn');
    const progressSection = document.getElementById('progressSection');
    const resultsSection = document.getElementById('resultsSection');

    // Disable button and show spinner
    processBtn.disabled = true;
    processBtn.querySelector('.btn-text').textContent = 'Processing...';
    processBtn.querySelector('.spinner').style.display = 'inline-block';

    // Show progress
    progressSection.style.display = 'block';
    resultsSection.style.display = 'none';
    updateProgress(10, 'Uploading audio file...');

    try {
        // Prepare form data
        const formData = new FormData();
        const audioFile = document.getElementById('audioFile').files[0];

        if (!audioFile) {
            throw new Error('Please select an audio file');
        }

        formData.append('file', audioFile);

        // Meeting metadata
        const metadata = {
            title: document.getElementById('meetingTitle').value,
            date: document.getElementById('meetingDate').value || new Date().toISOString().split('T')[0],
            participants: document.getElementById('participants').value.split(',').map(p => p.trim()).filter(p => p),
            agenda: document.getElementById('agenda').value
        };
        formData.append('metadata', JSON.stringify(metadata));

        // Template and formats
        formData.append('template', document.getElementById('template').value);

        const formats = Array.from(document.querySelectorAll('input[name="format"]:checked'))
            .map(cb => cb.value);
        formData.append('formats', formats.join(','));

        // Language
        formData.append('language', document.getElementById('language').value);

        updateProgress(20, 'Transcribing audio with Whisper...');

        // Make API call
        const response = await fetch('/api/process-meeting', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Processing failed');
        }

        updateProgress(70, 'Analyzing with Gemini AI...');

        const result = await response.json();

        updateProgress(90, 'Generating documents...');

        // Display results
        displayResults(result);

        updateProgress(100, 'Complete!');

        // Hide progress, show results
        setTimeout(() => {
            progressSection.style.display = 'none';
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }, 1000);

    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
        progressSection.style.display = 'none';
    } finally {
        // Re-enable button
        processBtn.disabled = false;
        processBtn.querySelector('.btn-text').textContent = '🚀 Process Meeting';
        processBtn.querySelector('.spinner').style.display = 'none';
    }
}

function updateProgress(percent, text) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    progressBar.style.width = percent + '%';
    progressBar.textContent = percent + '%';
    progressText.textContent = text;
}

function displayResults(result) {
    // Transcript
    document.getElementById('transcriptBox').textContent = result.transcript;

    // Action Items
    const actionItemsBox = document.getElementById('actionItemsBox');
    if (result.analysis.action_items && result.analysis.action_items.length > 0) {
        actionItemsBox.innerHTML = result.analysis.action_items.map(item => `
            <div class="action-item">
                <div class="action-item-header">${item.description}</div>
                <div class="action-item-meta">
                    <span>👤 <strong>Owner:</strong> ${item.owner || 'Unassigned'}</span>
                    <span>📅 <strong>Due:</strong> ${item.due_date || 'Not specified'}</span>
                    <span><span class="badge badge-${item.priority || 'medium'}">${(item.priority || 'medium').toUpperCase()}</span></span>
                </div>
                ${item.context ? `<div style="margin-top: 10px; font-size: 0.9rem; color: #6B7280;">Context: ${item.context}</div>` : ''}
            </div>
        `).join('');
    } else {
        actionItemsBox.innerHTML = '<p style="color: #6B7280;">No action items found.</p>';
    }

    // Decisions
    const decisionsBox = document.getElementById('decisionsBox');
    if (result.analysis.decisions && result.analysis.decisions.length > 0) {
        decisionsBox.innerHTML = result.analysis.decisions.map(decision => `
            <div class="decision-item">
                <div style="font-weight: 600; margin-bottom: 8px;">${decision.decision}</div>
                ${decision.rationale ? `<div style="font-size: 0.9rem; color: #6B7280; margin-bottom: 5px;"><strong>Rationale:</strong> ${decision.rationale}</div>` : ''}
                ${decision.stakeholders ? `<div style="font-size: 0.9rem; color: #6B7280;"><strong>Stakeholders:</strong> ${Array.isArray(decision.stakeholders) ? decision.stakeholders.join(', ') : decision.stakeholders}</div>` : ''}
            </div>
        `).join('');
    } else {
        decisionsBox.innerHTML = '<p style="color: #6B7280;">No key decisions recorded.</p>';
    }

    // Executive Summary
    const summaryBox = document.getElementById('summaryBox');
    if (result.analysis.executive_summary) {
        const summary = result.analysis.executive_summary;
        summaryBox.innerHTML = `
            <div class="summary-item">
                <h4 style="margin-bottom: 10px;">Overview</h4>
                <p style="line-height: 1.6;">${summary.overview || 'N/A'}</p>
            </div>
            ${summary.key_outcomes && summary.key_outcomes.length > 0 ? `
                <div class="summary-item">
                    <h4 style="margin-bottom: 10px;">Key Outcomes</h4>
                    <ul style="padding-left: 20px;">
                        ${summary.key_outcomes.map(outcome => `<li style="margin-bottom: 5px;">${outcome}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
    } else {
        summaryBox.innerHTML = '<p style="color: #6B7280;">Summary not available.</p>';
    }

    // Download Links
    const downloadLinks = document.getElementById('downloadLinks');
    if (result.minutes_files) {
        downloadLinks.innerHTML = Object.entries(result.minutes_files).map(([format, filepath]) => {
            const filename = filepath.split(/[/\\]/).pop();
            const icons = {
                pdf: '📄',
                markdown: '📝',
                txt: '📃',
                docx: '📘'
            };

            return `
                <a href="/api/download/${filename}" class="download-card" download>
                    <div class="download-icon">${icons[format] || '📄'}</div>
                    <div style="font-weight: 600;">${format.toUpperCase()}</div>
                    <div style="font-size: 0.85rem; color: #6B7280; margin-top: 5px;">Download ${format}</div>
                </a>
            `;
        }).join('');
    }
}

function copyTranscript() {
    const transcriptText = document.getElementById('transcriptBox').textContent;
    navigator.clipboard.writeText(transcriptText).then(() => {
        alert('Transcript copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Set today's date as default
document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('meetingDate');
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;

    // Check API health
    checkHealth();
});

async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const health = await response.json();

        const mainElement = document.querySelector('main');
        const firstCard = document.querySelector('.card');

        // Check for missing API keys
        const missingKeys = [];

        if (!health.gemini_configured) {
            missingKeys.push({
                name: 'Gemini API',
                url: 'https://makersuite.google.com/app/apikey',
                envVar: 'GEMINI_API_KEY'
            });
        }

        if (!health.assemblyai_configured) {
            missingKeys.push({
                name: 'AssemblyAI API',
                url: 'https://www.assemblyai.com/dashboard/signup',
                envVar: 'ASSEMBLYAI_API_KEY'
            });
        }

        if (missingKeys.length > 0) {
            const warning = document.createElement('div');
            warning.className = 'alert alert-warning';

            let html = '⚠️ <strong>API Keys Required!</strong> To use this app, you need <strong>2 FREE API keys</strong>:<br><br>';

            missingKeys.forEach((key, index) => {
                html += `<strong>${index + 1}. ${key.name}</strong><br>`;
                html += `→ Get it FREE at: <a href="${key.url}" target="_blank" style="color: #1976D2; text-decoration: underline;">${key.url}</a><br>`;
                html += `→ Add to <code>.env</code> file as: <code>${key.envVar}=your-key-here</code><br><br>`;
            });

            html += '<strong>📝 Quick Setup:</strong><br>';
            html += '1. Get both API keys (links above - takes 5 minutes)<br>';
            html += '2. Copy <code>.env.simple</code> to <code>.env</code><br>';
            html += '3. Paste your API keys in the <code>.env</code> file<br>';
            html += '4. Restart the app<br><br>';
            html += '<em>You can explore the UI now, but processing requires the API keys!</em>';

            warning.innerHTML = html;
            mainElement.insertBefore(warning, firstCard);
        } else {
            // All configured - show success message
            const success = document.createElement('div');
            success.className = 'alert alert-success';
            success.innerHTML = '✅ <strong>Ready to go!</strong> All API keys configured. Upload a meeting recording to get started!';
            mainElement.insertBefore(success, firstCard);
        }

        console.log('System Status:', health);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

// Auto-fill today's date for easy prototyping
document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('meetingDate');
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
});
