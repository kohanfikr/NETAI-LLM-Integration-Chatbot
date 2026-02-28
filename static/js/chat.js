/**
 * NETAI Chatbot — Frontend JavaScript
 * Handles chat interactions, network context, and UI state.
 */

const API_BASE = '/api/v1';
let conversationId = null;
let isProcessing = false;

// ─── Initialization ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadNetworkNodes();
    loadNetworkStatus();
    loadServiceInfo();
    setupInputHandlers();
});

function setupInputHandlers() {
    const input = document.getElementById('chat-input');

    // Auto-resize textarea
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    });

    // Send on Enter (Shift+Enter for new line)
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Update model display
    document.getElementById('model-select').addEventListener('change', (e) => {
        const modelNames = {
            'qwen3-vl': 'Qwen3-VL',
            'glm-4.7': 'GLM-4.7',
            'gpt-oss': 'GPT-OSS'
        };
        document.getElementById('current-model').textContent = modelNames[e.target.value] || e.target.value;
    });
}

// ─── Chat Functions ──────────────────────────────────────────────

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message || isProcessing) return;

    // Clear welcome message on first interaction
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // Add user message to chat
    appendMessage('user', message);
    input.value = '';
    input.style.height = 'auto';

    // Show typing indicator
    const typingId = showTyping();
    isProcessing = true;
    document.getElementById('send-btn').disabled = true;

    try {
        const model = document.getElementById('model-select').value;
        const source = document.getElementById('source-node').value || null;
        const dest = document.getElementById('dest-node').value || null;

        const response = await fetch(`${API_BASE}/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId,
                model: model,
                source: source,
                destination: dest,
            }),
        });

        removeTyping(typingId);

        if (!response.ok) {
            const error = await response.json();
            appendMessage('assistant', `⚠️ Error: ${error.detail || 'Request failed'}`);
            return;
        }

        const data = await response.json();
        conversationId = data.conversation_id;
        appendMessage('assistant', data.message.content);

    } catch (error) {
        removeTyping(typingId);
        appendMessage('assistant', `⚠️ Connection error: ${error.message}`);
    } finally {
        isProcessing = false;
        document.getElementById('send-btn').disabled = false;
    }
}

function sendQuickAction(message) {
    document.getElementById('chat-input').value = message;
    sendMessage();
}

// ─── Message Rendering ──────────────────────────────────────────

function appendMessage(role, content) {
    const container = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;

    const avatar = role === 'assistant' ? '🔬' : '👤';
    const renderedContent = role === 'assistant' ? renderMarkdown(content) : escapeHtml(content);

    msgDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${renderedContent}</div>
    `;

    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function renderMarkdown(text) {
    // Basic markdown rendering
    return text
        // Headers
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Inline code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Unordered lists
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/((<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>')
        // Ordered lists
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        // Paragraphs
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ─── Typing Indicator ───────────────────────────────────────────

let typingCounter = 0;

function showTyping() {
    const id = `typing-${++typingCounter}`;
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message assistant';
    div.innerHTML = `
        <div class="message-avatar">🔬</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ─── Network Functions ──────────────────────────────────────────

async function loadNetworkNodes() {
    try {
        const response = await fetch(`${API_BASE}/network/nodes`);
        if (!response.ok) return;
        const data = await response.json();

        const sourceSelect = document.getElementById('source-node');
        const destSelect = document.getElementById('dest-node');

        data.nodes.forEach(node => {
            sourceSelect.add(new Option(node, node));
            destSelect.add(new Option(node, node));
        });
    } catch (e) {
        console.warn('Failed to load network nodes:', e);
    }
}

async function loadNetworkStatus() {
    try {
        const response = await fetch(`${API_BASE}/network/summary`);
        if (!response.ok) return;
        const data = await response.json();

        const statusDiv = document.getElementById('network-status');
        statusDiv.innerHTML = `
            <h3>Network Health</h3>
            <div class="status-grid">
                <div class="status-item">
                    <span class="status-dot healthy"></span>
                    <span>Healthy: ${data.healthy}</span>
                </div>
                <div class="status-item">
                    <span class="status-dot warning"></span>
                    <span>Warning: ${data.warning}</span>
                </div>
                <div class="status-item">
                    <span class="status-dot degraded"></span>
                    <span>Degraded: ${data.degraded}</span>
                </div>
                <div class="status-item">
                    <span class="status-dot critical"></span>
                    <span>Critical: ${data.critical}</span>
                </div>
            </div>
        `;
    } catch (e) {
        console.warn('Failed to load network status:', e);
    }
}

async function loadServiceInfo() {
    try {
        const response = await fetch(`${API_BASE}/info`);
        if (!response.ok) return;
        const data = await response.json();
        document.getElementById('app-version').textContent = `v${data.version}`;
    } catch (e) {
        console.warn('Failed to load service info:', e);
    }
}

// ─── UI Functions ───────────────────────────────────────────────

function clearChat() {
    conversationId = null;
    const container = document.getElementById('chat-messages');
    container.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🔬</div>
            <h2>Welcome to NETAI</h2>
            <p>I'm your AI-powered network diagnostics assistant for the National Research Platform.
               I can help you analyze network performance, diagnose anomalies, and suggest remediation strategies.</p>
            <div class="welcome-suggestions">
                <button onclick="sendQuickAction('What can you help me with?')">
                    What can you help me with?
                </button>
                <button onclick="sendQuickAction('Show me the network health overview')">
                    Network health overview
                </button>
                <button onclick="sendQuickAction('Explain the latency between UCSD and UChicago')">
                    Analyze latency
                </button>
            </div>
        </div>
    `;
}

function toggleDarkMode() {
    document.body.classList.toggle('light-mode');
}
