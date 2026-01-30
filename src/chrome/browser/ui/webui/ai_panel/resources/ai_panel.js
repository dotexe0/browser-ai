/**
 * AI Automation Panel - Main Controller
 *
 * Orchestrates the automation UI, provider management, and execution flow.
 * All AI and automation calls go through NativeMessagingHelper to the C++ service.
 */

class AutomationPanel {
  constructor(nativeMessaging) {
    this.native = nativeMessaging;
    this.providerManager = new AIProviderManager(nativeMessaging);
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

    // Check provider status
    this.updateProviderStatus();
    this.log('AI panel initialized', 'success');
  }

  /**
   * Populate provider dropdown from C++ service status
   */
  populateProviderDropdown() {
    const select = document.getElementById('provider-select');
    const status = this.providerManager.getProviderStatus();

    select.innerHTML = '';

    for (const [name, info] of Object.entries(status)) {
      const option = document.createElement('option');
      option.value = name;
      option.textContent = name;

      if (info.type === 'cloud' && !info.has_key) {
        option.textContent += ' (needs API key)';
      }
      if (info.type === 'local' && !info.available) {
        option.textContent += ' (not running)';
      }

      select.appendChild(option);
    }

    // Set current selection
    const active = this.providerManager.getActiveProvider();
    if (active) {
      select.value = active;
      this.updateProviderInfo(active);
    }
  }

  /**
   * Update provider info display
   */
  updateProviderInfo(providerName) {
    const infoDiv = document.getElementById('provider-info');
    const apiKeySection = document.getElementById('api-key-section');
    const status = this.providerManager.getProviderStatus();
    const info = status[providerName];

    if (!info) return;

    let infoText = '';
    if (info.type === 'cloud') {
      infoText = info.has_key ? 'API key configured' : 'Requires API key';
      apiKeySection.classList.remove('hidden');
    } else {
      infoText = info.available ? 'Local model available' : 'Not running';
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
      this.log('Conversation history cleared', 'info');
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
    this.providerManager.setActiveProvider(providerName);
    this.updateProviderInfo(providerName);
    this.updateProviderStatus();
  }

  /**
   * Toggle API key visibility
   */
  toggleApiKeyVisibility() {
    const input = document.getElementById('api-key-input');
    const btn = document.getElementById('toggle-api-key');

    if (input.type === 'password') {
      input.type = 'text';
      btn.textContent = 'Hide';
    } else {
      input.type = 'password';
      btn.textContent = 'Show';
    }
  }

  /**
   * Save API key via C++ Credential Store
   */
  async saveApiKey() {
    const providerName = this.providerManager.getActiveProvider();
    const apiKey = document.getElementById('api-key-input').value.trim();
    const statusDiv = document.getElementById('api-key-status');

    if (!apiKey) {
      this.showStatus(statusDiv, 'Please enter an API key', 'error');
      return;
    }

    try {
      await this.providerManager.storeApiKey(providerName, apiKey);
      this.showStatus(statusDiv, 'API key saved successfully', 'success');
      this.updateProviderStatus();
      this.populateProviderDropdown();
      this.log(`API key configured for ${providerName}`, 'success');
    } catch (error) {
      this.showStatus(statusDiv, `Error: ${error.message}`, 'error');
    }
  }

  /**
   * Capture screen via native messaging
   */
  async captureScreen() {
    this.log('Capturing screen...', 'info');
    this.setAutomationStatus('working');

    try {
      const captureData = await this.native.captureScreen();
      this.currentScreenshot = captureData.screenshot || '';

      const uiData = await this.native.inspectUI();
      this.currentUITree = uiData.uiTree || {};

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
   * Execute automation — request actions from AI via C++ service
   */
  async executeAutomation() {
    const userRequest = (document.getElementById('user-request').value || '').trim();

    if (!userRequest) {
      this.log('Please enter an automation request', 'warning');
      return;
    }

    this.log(`Processing request: "${userRequest}"`, 'info');
    this.setAutomationStatus('working');
    document.getElementById('execute-btn').disabled = true;

    try {
      this.log('Requesting actions from AI provider...', 'info');
      const result = await this.providerManager.getActions(userRequest);

      if (result.status === 'error' || result.error) {
        throw new Error(result.error || 'AI request failed');
      }

      const actions = result.actions || [];
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
   * Confirm and execute actions via native messaging
   */
  async confirmAndExecuteActions() {
    if (!this.plannedActions || this.plannedActions.length === 0) {
      return;
    }

    this.log('Executing actions...', 'info');
    this.setAutomationStatus('working');
    document.getElementById('actions-section').classList.add('hidden');

    try {
      const result = await this.native.executeActions(this.plannedActions);

      if (result.success) {
        this.log('All actions executed successfully', 'success');
      } else {
        this.log(`Execution error: ${result.error || 'Unknown error'}`, 'error');
      }

      this.setAutomationStatus('ready');
      this.plannedActions = null;
      // Clear screenshot so next request captures fresh
      this.currentScreenshot = null;
      this.currentUITree = null;
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
   * Display planned actions
   */
  displayActions(actions) {
    const section = document.getElementById('actions-section');
    const list = document.getElementById('actions-list');

    list.innerHTML = '';

    actions.forEach((action, index) => {
      const item = document.createElement('div');
      item.className = 'action-item';

      item.innerHTML = `
        <div class="action-details">
          <div class="action-type">${index + 1}. ${action.action.toUpperCase()}</div>
          <div class="action-params">${JSON.stringify(action.params)}</div>
        </div>
        <div class="action-confidence">
          ${Math.round((action.confidence || 0.7) * 100)}% confident
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
    const active = this.providerManager.getActiveProvider();
    const status = this.providerManager.getProviderStatus();
    const info = status[active];

    if (info) {
      const ready = info.type === 'local' ? info.available : info.has_key;
      badge.textContent = `Provider: ${active}`;
      badge.className = ready ? 'status-badge ready' : 'status-badge error';
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
  const native = new NativeMessagingHelper();
  const panel = new AutomationPanel(native);
  await panel.providerManager.ready;
  panel.initializeUI();
  panel.updateProviderStatus();
  window.automationPanel = panel;
});
