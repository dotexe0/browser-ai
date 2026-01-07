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
    
    this.initializeUI();
    this.attachEventListeners();
    this.updateProviderStatus();
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
  saveApiKey() {
    const providerName = this.providerManager.getActiveProvider().name;
    const apiKey = document.getElementById('api-key-input').value.trim();
    const statusDiv = document.getElementById('api-key-status');
    
    if (!apiKey) {
      this.showStatus(statusDiv, 'Please enter an API key', 'error');
      return;
    }
    
    try {
      this.providerManager.configureProvider(providerName, apiKey);
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
   * Capture screen (stub - will connect to automation service)
   */
  async captureScreen() {
    this.log('Capturing screen...', 'info');
    this.setAutomationStatus('working');
    
    try {
      // TODO: This will call the automation service via Native Messaging
      // For now, simulate with a stub
      const response = await this.simulateCaptureScreen();
      
      this.currentScreenshot = response.screenshot;
      this.currentUITree = response.uiTree;
      
      this.displayScreenPreview(response.screenshot);
      this.displayUITree(response.uiTree);
      
      this.log('Screen captured successfully', 'success');
      this.setAutomationStatus('ready');
    } catch (error) {
      this.log(`Error capturing screen: ${error.message}`, 'error');
      this.setAutomationStatus('error');
    }
  }

  /**
   * Execute automation
   */
  async executeAutomation() {
    const userRequest = document.getElementById('user-request').value.trim();
    
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
   * Confirm and execute actions
   */
  async confirmAndExecuteActions() {
    if (!this.plannedActions || this.plannedActions.length === 0) {
      return;
    }
    
    this.log('Executing actions...', 'info');
    this.setAutomationStatus('working');
    
    // Hide actions panel
    document.getElementById('actions-section').classList.add('hidden');
    
    try {
      // TODO: Send actions to automation service for execution
      // For now, simulate execution
      for (let i = 0; i < this.plannedActions.length; i++) {
        const action = this.plannedActions[i];
        this.log(`Executing: ${action.action} ${JSON.stringify(action.params)}`, 'info');
        await this.simulateActionExecution(action);
      }
      
      this.log('All actions executed successfully', 'success');
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

  /**
   * Simulate screen capture (stub for development)
   * @private
   */
  async simulateCaptureScreen() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          screenshot: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', // 1x1 placeholder
          uiTree: {
            type: 'desktop',
            elements: [
              {
                id: 'elem_1',
                name: 'File Explorer',
                type: 'Window',
                bounds: { x: 100, y: 100, width: 800, height: 600 },
                enabled: true
              },
              {
                id: 'elem_2',
                name: 'Search',
                type: 'TextBox',
                bounds: { x: 200, y: 150, width: 400, height: 30 },
                enabled: true
              }
            ]
          }
        });
      }, 500);
    });
  }

  /**
   * Simulate action execution (stub for development)
   * @private
   */
  async simulateActionExecution(action) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ success: true });
      }, 300);
    });
  }
}

// Initialize the panel when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.automationPanel = new AutomationPanel();
});
