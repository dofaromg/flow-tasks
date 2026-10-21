/**
 * MRL_AGI Web Application
 * Origin Signature: MrLiouWord
 *
 * Production-ready web UI for MRL_AI_SYSTEM
 * Integrates with P0 modules: runtime_config, memory_integration,
 * task_orchestrator, result_gating
 */

'use strict';

// Application State
const AppState = {
    apiUrl: 'http://localhost:7771',
    authToken: '',
    currentSessionId: null,
    sessions: [],
    model: '',
    runtimeMode: 'development',
};

// API Client
class APIClient {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.token = token;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async getHealth() {
        return this.request('/health');
    }

    async getSessions() {
        return this.request('/sessions');
    }

    async createSession(systemPrompt = '', label = '') {
        return this.request('/sessions', {
            method: 'POST',
            body: JSON.stringify({ system_prompt: systemPrompt, label }),
        });
    }

    async getSession(sessionId) {
        return this.request(`/sessions/${sessionId}`);
    }

    async deleteSession(sessionId) {
        return this.request(`/sessions/${sessionId}`, {
            method: 'DELETE',
        });
    }

    async sendMessage(message, sessionId = null, model = '') {
        const body = { message };
        if (sessionId) body.session_id = sessionId;
        if (model) body.model = model;

        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    async runAgentTask(goal, taskType = 'simple', agents = null) {
        const body = { goal, type: taskType };
        if (agents) body.agents = agents;

        return this.request('/agent/run', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }
}

// UI Controller
class UIController {
    constructor() {
        this.api = new APIClient(AppState.apiUrl, AppState.authToken);
        this.initElements();
        this.attachEventListeners();
        this.loadSettings();
        this.initialize();
    }

    initElements() {
        this.elements = {
            // Settings
            settingsBtn: document.getElementById('settings-btn'),
            settingsPanel: document.getElementById('settings-panel'),
            closeSettingsBtn: document.getElementById('close-settings-btn'),
            saveSettingsBtn: document.getElementById('save-settings-btn'),
            apiUrlInput: document.getElementById('api-url'),
            authTokenInput: document.getElementById('auth-token'),
            modelSelect: document.getElementById('model-select'),

            // Sessions
            newSessionBtn: document.getElementById('new-session-btn'),
            sessionList: document.getElementById('session-list'),

            // Chat
            chatContainer: document.getElementById('chat-container'),
            chatTitle: document.getElementById('chat-title'),
            messages: document.getElementById('messages'),
            messageInput: document.getElementById('message-input'),
            sendBtn: document.getElementById('send-btn'),
            sendBtnText: document.getElementById('send-btn-text'),
            clearChatBtn: document.getElementById('clear-chat-btn'),

            // Task Panel
            taskPanel: document.getElementById('task-panel'),
            closeTaskBtn: document.getElementById('close-task-btn'),
            taskGoalInput: document.getElementById('task-goal'),
            taskTypeSelect: document.getElementById('task-type'),
            taskAgentsInput: document.getElementById('task-agents'),
            agentsGroup: document.getElementById('agents-group'),
            submitTaskBtn: document.getElementById('submit-task-btn'),
            taskResult: document.getElementById('task-result'),

            // Status
            runtimeMode: document.getElementById('runtime-mode'),
            statusBar: document.getElementById('status-bar'),
            statusText: document.getElementById('status-text'),
        };
    }

    attachEventListeners() {
        // Settings
        this.elements.settingsBtn.addEventListener('click', () => this.showSettings());
        this.elements.closeSettingsBtn.addEventListener('click', () => this.hideSettings());
        this.elements.saveSettingsBtn.addEventListener('click', () => this.saveSettings());

        // Sessions
        this.elements.newSessionBtn.addEventListener('click', () => this.createNewSession());

        // Chat
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.elements.clearChatBtn.addEventListener('click', () => this.clearChat());

        // Task Panel
        this.elements.closeTaskBtn.addEventListener('click', () => this.hideTaskPanel());
        this.elements.submitTaskBtn.addEventListener('click', () => this.submitTask());
        this.elements.taskTypeSelect.addEventListener('change', (e) => {
            this.elements.agentsGroup.style.display =
                e.target.value === 'multi_agent' ? 'block' : 'none';
        });

        // Auto-resize textarea
        this.elements.messageInput.addEventListener('input', () => {
            this.elements.messageInput.style.height = 'auto';
            this.elements.messageInput.style.height =
                Math.min(this.elements.messageInput.scrollHeight, 200) + 'px';
        });
    }

    async initialize() {
        this.setStatus('Connecting to API...');
        try {
            const health = await this.api.getHealth();
            AppState.runtimeMode = health.runtime_mode || 'development';
            this.elements.runtimeMode.textContent = `Mode: ${AppState.runtimeMode}`;
            this.setStatus('Connected', 'success');
            await this.loadSessions();
        } catch (error) {
            this.setStatus(`Failed to connect: ${error.message}`, 'error');
            console.error('Initialization failed:', error);
        }
    }

    // Settings
    loadSettings() {
        const saved = localStorage.getItem('mrl_settings');
        if (saved) {
            const settings = JSON.parse(saved);
            AppState.apiUrl = settings.apiUrl || AppState.apiUrl;
            AppState.authToken = settings.authToken || '';
            AppState.model = settings.model || '';

            this.elements.apiUrlInput.value = AppState.apiUrl;
            this.elements.authTokenInput.value = AppState.authToken;
            this.elements.modelSelect.value = AppState.model;

            this.api = new APIClient(AppState.apiUrl, AppState.authToken);
        }
    }

    saveSettings() {
        AppState.apiUrl = this.elements.apiUrlInput.value;
        AppState.authToken = this.elements.authTokenInput.value;
        AppState.model = this.elements.modelSelect.value;

        localStorage.setItem('mrl_settings', JSON.stringify({
            apiUrl: AppState.apiUrl,
            authToken: AppState.authToken,
            model: AppState.model,
        }));

        this.api = new APIClient(AppState.apiUrl, AppState.authToken);
        this.hideSettings();
        this.setStatus('Settings saved', 'success');
        this.initialize();
    }

    showSettings() {
        this.elements.settingsPanel.style.display = 'flex';
    }

    hideSettings() {
        this.elements.settingsPanel.style.display = 'none';
    }

    // Sessions
    async loadSessions() {
        try {
            const response = await this.api.getSessions();
            AppState.sessions = response.sessions || [];
            this.renderSessions();
        } catch (error) {
            console.error('Failed to load sessions:', error);
            this.setStatus(`Failed to load sessions: ${error.message}`, 'error');
        }
    }

    renderSessions() {
        if (AppState.sessions.length === 0) {
            this.elements.sessionList.innerHTML = '<div class="loading">No sessions yet</div>';
            return;
        }

        this.elements.sessionList.innerHTML = AppState.sessions.map(session => `
            <div class="session-item ${session.session_id === AppState.currentSessionId ? 'active' : ''}"
                 data-session-id="${session.session_id}">
                <div class="session-title">${session.label || 'Conversation'}</div>
                <div class="session-meta">${session.turn_count} turns</div>
            </div>
        `).join('');

        // Attach click listeners
        this.elements.sessionList.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', () => {
                this.loadSession(item.dataset.sessionId);
            });
        });
    }

    async createNewSession() {
        try {
            this.setStatus('Creating new session...');
            const systemPrompt = 'You are MRL_AGI, a production-grade private AI assistant. Origin signature: MrLiouWord.';
            const label = `Chat ${new Date().toLocaleString()}`;
            const response = await this.api.createSession(systemPrompt, label);

            AppState.currentSessionId = response.session_id;
            await this.loadSessions();
            this.clearChat();
            this.setStatus('New session created', 'success');
        } catch (error) {
            this.setStatus(`Failed to create session: ${error.message}`, 'error');
        }
    }

    async loadSession(sessionId) {
        try {
            this.setStatus('Loading session...');
            const response = await this.api.getSession(sessionId);
            AppState.currentSessionId = sessionId;

            this.elements.messages.innerHTML = '';
            response.messages.forEach(msg => {
                this.addMessage(msg.role, msg.content, msg);
            });

            this.renderSessions();
            this.setStatus('Session loaded', 'success');
        } catch (error) {
            this.setStatus(`Failed to load session: ${error.message}`, 'error');
        }
    }

    // Chat
    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message) return;

        this.elements.messageInput.value = '';
        this.elements.messageInput.style.height = 'auto';
        this.elements.sendBtn.disabled = true;
        this.elements.sendBtnText.textContent = 'Sending...';

        // Add user message to UI
        this.addMessage('user', message);

        try {
            const response = await this.api.sendMessage(
                message,
                AppState.currentSessionId,
                AppState.model
            );

            // Update current session if new
            if (response.session_id && !AppState.currentSessionId) {
                AppState.currentSessionId = response.session_id;
                await this.loadSessions();
            }

            // Add assistant response
            this.addMessage('assistant', response.reply, {
                model: response.model,
                engine: response.engine,
                runtime_mode: response.runtime_mode,
                runtime_origin: response.runtime_origin,
                trace_id: response.trace_id,
            });

            this.setStatus('Message sent', 'success');
        } catch (error) {
            this.addMessage('system', `Error: ${error.message}`, { error: true });
            this.setStatus(`Failed to send message: ${error.message}`, 'error');
        } finally {
            this.elements.sendBtn.disabled = false;
            this.elements.sendBtnText.textContent = 'Send';
        }
    }

    addMessage(role, content, meta = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = {
            user: 'U',
            assistant: 'AI',
            system: 'S',
        }[role] || '?';

        let metaInfo = '';
        if (meta.model) {
            metaInfo += `<span>Model: ${meta.model}</span>`;
        }
        if (meta.engine) {
            metaInfo += `<span>Engine: ${meta.engine}</span>`;
        }
        if (meta.runtime_mode) {
            metaInfo += `<span>Mode: ${meta.runtime_mode}</span>`;
        }
        if (meta.trace_id) {
            metaInfo += `<span>Trace: ${meta.trace_id.substring(0, 8)}...</span>`;
        }

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-role">${role.charAt(0).toUpperCase() + role.slice(1)}</div>
                <div class="message-text">${this.escapeHtml(content)}</div>
                ${metaInfo ? `<div class="message-meta">${metaInfo}</div>` : ''}
            </div>
        `;

        this.elements.messages.appendChild(messageDiv);
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    clearChat() {
        this.elements.messages.innerHTML = '';
        AppState.currentSessionId = null;
        this.renderSessions();
    }

    // Task Panel
    showTaskPanel() {
        this.elements.taskPanel.style.display = 'flex';
    }

    hideTaskPanel() {
        this.elements.taskPanel.style.display = 'none';
    }

    async submitTask() {
        const goal = this.elements.taskGoalInput.value.trim();
        if (!goal) {
            alert('Please enter a task goal');
            return;
        }

        const taskType = this.elements.taskTypeSelect.value;
        const agentsInput = this.elements.taskAgentsInput.value.trim();
        const agents = agentsInput ? agentsInput.split(',').map(a => a.trim()) : null;

        this.elements.submitTaskBtn.disabled = true;
        this.elements.submitTaskBtn.textContent = 'Submitting...';

        try {
            const response = await this.api.runAgentTask(goal, taskType, agents);

            this.elements.taskResult.style.display = 'block';
            this.elements.taskResult.innerHTML = `
                <h3>Task Result</h3>
                <pre>${JSON.stringify(response, null, 2)}</pre>
            `;

            this.setStatus('Task submitted successfully', 'success');
        } catch (error) {
            this.elements.taskResult.style.display = 'block';
            this.elements.taskResult.innerHTML = `
                <div class="error-message">
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
            this.setStatus(`Task failed: ${error.message}`, 'error');
        } finally {
            this.elements.submitTaskBtn.disabled = false;
            this.elements.submitTaskBtn.textContent = 'Submit Task';
        }
    }

    // Utility
    setStatus(message, type = '') {
        this.elements.statusText.textContent = message;
        this.elements.statusBar.className = `status-bar ${type}`;

        if (type) {
            setTimeout(() => {
                this.elements.statusBar.className = 'status-bar';
                this.elements.statusText.textContent = 'Ready';
            }, 3000);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    new UIController();
});