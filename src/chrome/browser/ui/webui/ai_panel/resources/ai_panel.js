/**
 * AI Automation Panel - Main Controller
 * 
 * Orchestrates the automation UI, provider management, and execution flow.
 */

class AutomationPanel {
  constructor() {
    this.providerManager = new AIProviderManager();
    this.currentScreenshot = null;
    this.currentUITree = null;
    this.plannedActions = null;

    this.attachEventListeners();
  }

  /**
   * Initialize UI elements
   */
  initializeUI() {
    // Populate provider dropdown
    this.populateProviderDropdown();
    
    // Check if active provider is configured
    const activeProvider = this.providerManager.getActiveProvider();
    if (activeProvider && activeProvider.isConfigured()) {
      this.enableAutomation();
      this.log('AI provider configured and ready', 'success');
    } else {
      this.log('Please configure an AI provider in settings', 'warning');
    }
  }

  /**
   * Populate provider dropdown
   */
  populateProviderDropdown() {
    const select = document.getElementById('provider-select');
    const providers = this.providerManager.getAvailableProviders();
    
    select.innerHTML = '';
    
    providers.forEach(provider => {
      const option = document.createElement('option');
      option.value = provider.name;
      option.textContent = provider.name;
      
      // Mark if not configured
      if (!provider.configured && provider.requiresApiKey) {
        option.textContent += ' (needs API key)';
      }
      
      select.appendChild(option);
    });
    
    // Set current selection
    const activeProvider = this.providerManager.getActiveProvider();
    if (activeProvider) {
      select.value = activeProvider.name;
      this.updateProviderInfo(activeProvider.name);
    }
  }

  /**
   * Update provider info display
   */
  updateProviderInfo(providerName) {
    const provider = this.providerManager.getProvider(providerName);
    const infoDiv = document.getElementById('provider-info');
    const apiKeySection = document.getElementById('api-key-section');
    
    if (!provider) return;
    
    // Show provider info
    let infoText = provider.supportsVision ? '✓ Supports vision' : '✗ No vision support';
    if (provider.requiresApiKey) {
      infoText += ' | Requires API key';
      apiKeySection.classList.remove('hidden');
    } else {
      infoText += ' | No API key needed';
      apiKeySection.classList.add('hidden');
    }
    
    infoDiv.textContent = infoText;
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    // Settings button
    document.getElementById('settings-btn').addEventListener('click', () => {
      this.toggleSettings();
    });
    
    document.getElementById('close-settings').addEventListener('click', () => {
      this.toggleSettings();
    });
    
    // Provider selection
    document.getElementById('provider-select').addEventListener('change', (e) => {
      this.onProviderChanged(e.target.value);
    });
    
    // API key management
    document.getElementById('toggle-api-key').addEventListener('click', () => {
      this.toggleApiKeyVisibility();
    });
    
    document.getElementById('save-api-key').addEventListener('click', () => {
      this.saveApiKey();
    });
    
    // Clear history
    document.getElementById('clear-history').addEventListener('click', () => {
      this.clearConversationHistory();
    });
    
    // Automation controls
    document.getElementById('execute-btn').addEventListener('click', () => {
      this.executeAutomation();
    });
    
    document.getElementById('capture-screen-btn').addEventListener('click', () => {
      this.captureScreen();
    });
    
    // Actions confirmation
    document.getElementById('confirm-actions-btn').addEventListener('click', () => {
      this.confirmAndExecuteActions();
    });
    
    document.getElementById('cancel-actions-btn').addEventListener('click', () => {
      this.cancelActions();
    });
    
    // Log management
    document.getElementById('clear-log').addEventListener('click', () => {
      this.clearLog();
    });
  }

  /**
   * Toggle settings panel
   */
  toggleSettings() {
    const settingsPanel = document.getElementById('settings-panel');
    const mainPanel = document.getElementById('main-panel');
    
    settingsPanel.classList.toggle('hidden');
    mainPanel.classList.toggle('hidden');
  }

  /**
   * Handle provider change
   */
  onProviderChanged(providerName) {
    this.log(`Switching to provider: ${providerName}`, 'info');
    
    if (this.providerManager.setActiveProvider(providerName)) {
      this.updateProviderInfo(providerName);
      this.updateProviderStatus();
      
      const provider = this.providerManager.getProvider(providerName);
      if (provider.isConfigured()) {
        this.enableAutomation();
        this.log(`Provider ${providerName} is ready`, 'success');
      } else {
        this.disableAutomation();
        this.log(`Provider ${providerName} requires configuration`, 'warning');
      }
    }
  }

  /**
   * Toggle API key visibility
   */
  toggleApiKeyVisibility() {
    const input = document.getElementById('api-key-input');
    const btn = document.getElementById('toggle-api-key');
    
    if (input.type === 'password') {
      input.type = 'text';
      btn.textContent = '🙈';
    } else {
      input.type = 'password';
      btn.textContent = '👁️';
    }
  }

  /**
   * Save API key
   */
  async saveApiKey() {
    const providerName = this.providerManager.getActiveProvider().name;
    const apiKey = document.getElementById('api-key-input').value.trim();
    const statusDiv = document.getElementById('api-key-status');

    if (!apiKey) {
      this.showStatus(statusDiv, 'Please enter an API key', 'error');
      return;
    }

    try {
      await this.providerManager.configureProvider(providerName, apiKey);
      this.showStatus(statusDiv, 'API key saved successfully', 'success');
      this.enableAutomation();
      this.updateProviderStatus();
      this.log(`API key configured for ${providerName}`, 'success');
    } catch (error) {
      this.showStatus(statusDiv, `Error: ${error.message}`, 'error');
    }
  }

  /**
   * Clear conversation history
   */
  clearConversationHistory() {
    this.providerManager.clearConversationHistory();
    this.log('Conversation history cleared', 'info');
  }

  /**
   * Capture screen via backend automation service
   */
  async captureScreen() {
    this.log('Capturing screen...', 'info');
    this.setAutomationStatus('working');

    try {
      const response = await fetch('http://localhost:5000/api/capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'capture' })
      });

      if (!response.ok) {
        throw new Error(`Capture failed: ${response.status}`);
      }

      const data = await response.json();
      this.currentScreenshot = data.screenshot || '';
      this.currentUITree = data.ui_tree || {};

      if (this.currentScreenshot) {
        this.displayScreenPreview(this.currentScreenshot);
      }
      this.displayUITree(this.currentUITree);

      this.log('Screen captured successfully', 'success');
      this.setAutomationStatus('ready');
    } catch (error) {
      this.log(`Error capturing screen: ${error.message}`, 'error');
      this.setAutomationStatus('error');
    }
  }

  /**
   * Sanitize user request input
   * @param {string} input
   * @returns {string}
   */
  sanitizeRequest(input) {
    let sanitized = (input || '').trim();
    sanitized = sanitized.slice(0, 2000);
    sanitized = sanitized.replace(/[^\P{Cc}\n]/gu, '');
    return sanitized;
  }

  /**
   * Execute automation
   */
  async executeAutomation() {
    const userRequest = this.sanitizeRequest(document.getElementById('user-request').value);
    
    if (!userRequest) {
      this.log('Please enter an automation request', 'warning');
      return;
    }
    
    this.log(`Processing request: "${userRequest}"`, 'info');
    this.setAutomationStatus('working');
    document.getElementById('execute-btn').disabled = true;
    
    try {
      // Capture screen if not already captured
      if (!this.currentScreenshot || !this.currentUITree) {
        await this.captureScreen();
      }
      
      // Get actions from AI provider
      this.log('Requesting actions from AI provider...', 'info');
      const actions = await this.providerManager.getActions({
        screenshot: this.currentScreenshot,
        uiTree: this.currentUITree,
        userRequest: userRequest
      });
      
      this.log(`AI returned ${actions.length} actions`, 'success');
      
      // Display actions for confirmation
      this.displayActions(actions);
      this.plannedActions = actions;
      
      this.setAutomationStatus('ready');
    } catch (error) {
      this.log(`Error: ${error.message}`, 'error');
      this.setAutomationStatus('error');
    } finally {
      document.getElementById('execute-btn').disabled = false;
    }
  }

  /**
   * Confirm and execute actions via backend
   */
  async confirmAndExecuteActions() {
    if (!this.plannedActions || this.plannedActions.length === 0) {
      return;
    }

    for (let i = 0; i < this.plannedActions.length; i++) {
      const validation = this.validateAction(this.plannedActions[i]);
      if (!validation.valid) {
        this.log(`Action ${i + 1} is invalid: ${validation.error}`, 'error');
        return;
      }
    }

    this.log('Executing actions...', 'info');
    this.setAutomationStatus('working');
    document.getElementById('actions-section').classList.add('hidden');

    try {
      const response = await fetch('http://localhost:5000/api/get-actions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: this.providerManager.getActiveProvider()?.providerId || 'ollama',
          screenshot: this.currentScreenshot || '',
          ui_tree: this.currentUITree || {},
          user_request: document.getElementById('user-request').value.trim(),
          execute: true,
          actions: this.plannedActions
        })
      });

      const data = await response.json();

      if (data.all_executed) {
        this.log('All actions executed successfully', 'success');
      } else if (data.execution_failed_at !== undefined) {
        this.log(`Execution failed at action ${data.execution_failed_at + 1}`, 'error');
      }

      this.setAutomationStatus('ready');
      this.plannedActions = null;
    } catch (error) {
      this.log(`Execution error: ${error.message}`, 'error');
      this.setAutomationStatus('error');
    }
  }

  /**
   * Cancel actions
   */
  cancelActions() {
    this.log('Actions cancelled', 'info');
    document.getElementById('actions-section').classList.add('hidden');
    this.plannedActions = null;
  }

  /**
   * Display screen preview
   */
  displayScreenPreview(screenshot) {
    const preview = document.getElementById('screenshot-preview');
    const section = document.getElementById('preview-section');
    
    preview.innerHTML = `<img src="data:image/png;base64,${screenshot}" alt="Screen capture">`;
    section.classList.remove('hidden');
  }

  /**
   * Display UI tree
   */
  displayUITree(uiTree) {
    const content = document.getElementById('ui-tree-content');
    content.textContent = JSON.stringify(uiTree, null, 2);
  }

  /**
   * Validate a single automation action
   * @param {Object} action
   * @returns {{valid: boolean, error?: string}}
   */
  validateAction(action) {
    const allowedTypes = ['click', 'type', 'scroll', 'press_keys', 'wait'];
    if (!action || !action.action || !allowedTypes.includes(action.action)) {
      return { valid: false, error: `Invalid action type: ${action?.action}` };
    }
    const params = action.params || {};
    switch (action.action) {
      case 'click': {
        const x = params.x;
        const y = params.y;
        if (typeof x !== 'number' || typeof y !== 'number') {
          return { valid: false, error: 'Click requires numeric x and y coordinates' };
        }
        if (x < 0 || x > 10000 || y < 0 || y > 10000) {
          return { valid: false, error: 'Click coordinates out of range (0-10000)' };
        }
        break;
      }
      case 'type': {
        const text = params.text;
        if (typeof text !== 'string' || text.length === 0) {
          return { valid: false, error: 'Type requires non-empty string text' };
        }
        if (text.length > 10000) {
          return { valid: false, error: 'Type text exceeds maximum length of 10000' };
        }
        break;
      }
      case 'wait': {
        const ms = params.ms;
        if (typeof ms !== 'number') {
          return { valid: false, error: 'Wait requires numeric ms value' };
        }
        if (ms < 0 || ms > 30000) {
          return { valid: false, error: 'Wait ms out of range (0-30000)' };
        }
        break;
      }
      case 'scroll': {
        const delta = params.delta;
        if (typeof delta !== 'number') {
          return { valid: false, error: 'Scroll requires numeric delta value' };
        }
        break;
      }
      case 'press_keys': {
        const keys = params.keys;
        if (!Array.isArray(keys) || keys.length === 0) {
          return { valid: false, error: 'press_keys requires non-empty keys array' };
        }
        break;
      }
    }
    return { valid: true };
  }

  /**
   * Display planned actions
   */
  displayActions(actions) {
    const section = document.getElementById('actions-section');
    const list = document.getElementById('actions-list');
    
    list.innerHTML = '';
    
    actions.forEach((action, index) => {
      const item = document.createElement('div');
      const validation = this.validateAction(action);
      item.className = 'action-item' + (validation.valid ? '' : ' invalid');

      item.innerHTML = `
        <div class="action-details">
          <div class="action-type">${index + 1}. ${action.action.toUpperCase()}${validation.valid ? '' : ' [INVALID]'}</div>
          <div class="action-params">${JSON.stringify(action.params)}</div>
          ${validation.valid ? '' : `<div class="action-error">${validation.error}</div>`}
        </div>
        <div class="action-confidence">
          ${Math.round(action.confidence * 100)}% confident
        </div>
      `;

      list.appendChild(item);
    });
    
    section.classList.remove('hidden');
  }

  /**
   * Update provider status badge
   */
  updateProviderStatus() {
    const badge = document.getElementById('provider-status');
    const activeProvider = this.providerManager.getActiveProvider();
    
    if (activeProvider && activeProvider.isConfigured()) {
      badge.textContent = `Provider: ${activeProvider.name}`;
      badge.className = 'status-badge ready';
    } else {
      badge.textContent = 'Not configured';
      badge.className = 'status-badge error';
    }
  }

  /**
   * Set automation status
   */
  setAutomationStatus(status) {
    const badge = document.getElementById('automation-status');
    const statusMap = {
      'ready': { text: 'Ready', class: 'ready' },
      'working': { text: 'Working...', class: 'working' },
      'error': { text: 'Error', class: 'error' }
    };
    
    const config = statusMap[status] || statusMap.ready;
    badge.textContent = config.text;
    badge.className = `status-badge ${config.class}`;
  }

  /**
   * Enable automation controls
   */
  enableAutomation() {
    document.getElementById('execute-btn').disabled = false;
  }

  /**
   * Disable automation controls
   */
  disableAutomation() {
    document.getElementById('execute-btn').disabled = true;
  }

  /**
   * Log message to output
   */
  log(message, type = 'info') {
    const logOutput = document.getElementById('log-output');
    const entry = document.createElement('p');
    entry.className = `log-entry ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    
    logOutput.appendChild(entry);
    logOutput.scrollTop = logOutput.scrollHeight;
  }

  /**
   * Clear log
   */
  clearLog() {
    const logOutput = document.getElementById('log-output');
    logOutput.innerHTML = '<p class="log-entry info">Log cleared</p>';
  }

  /**
   * Show status message
   */
  showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-message ${type}`;
    element.style.display = 'block';
    
    setTimeout(() => {
      element.style.display = 'none';
    }, 5000);
  }

}

// Initialize the panel when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  const panel = new AutomationPanel();
  await panel.providerManager.ready;
  panel.initializeUI();
  panel.updateProviderStatus();
  window.automationPanel = panel;
});
