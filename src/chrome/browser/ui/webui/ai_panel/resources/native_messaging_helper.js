/**
 * Native Messaging Helper
 * 
 * Handles communication with the C++ automation service via Chrome Native Messaging
 */

class NativeMessagingHelper {
  constructor() {
    this.hostName = 'com.browser_ai.automation';
    this.isConnected = false;
  }

  /**
   * Send a message to the native automation service
   * @param {Object} message - The message to send
   * @returns {Promise<Object>} - The response from the service
   */
  async sendMessage(message) {
    return new Promise((resolve, reject) => {
      try {
        // Check if chrome.runtime is available
        if (typeof chrome === 'undefined' || !chrome.runtime || !chrome.runtime.sendNativeMessage) {
          reject(new Error('Chrome Native Messaging API not available'));
          return;
        }

        chrome.runtime.sendNativeMessage(
          this.hostName,
          message,
          (response) => {
            if (chrome.runtime.lastError) {
              reject(new Error(`Native messaging error: ${chrome.runtime.lastError.message}`));
              return;
            }

            if (!response) {
              reject(new Error('No response from automation service'));
              return;
            }

            resolve(response);
          }
        );
      } catch (error) {
        reject(new Error(`Failed to send native message: ${error.message}`));
      }
    });
  }

  /**
   * Test connection to automation service
   * @returns {Promise<boolean>} - True if connected
   */
  async testConnection() {
    try {
      const response = await this.sendMessage({action: 'ping'});
      this.isConnected = response && response.success;
      return this.isConnected;
    } catch (error) {
      this.isConnected = false;
      throw error;
    }
  }

  /**
   * Get capabilities from automation service
   * @returns {Promise<Object>} - Service capabilities
   */
  async getCapabilities() {
    const response = await this.sendMessage({action: 'get_capabilities'});
    if (!response || !response.success) {
      throw new Error('Failed to get capabilities');
    }
    return response.capabilities;
  }

  /**
   * Capture screenshot
   * @returns {Promise<Object>} - Screenshot data {success, screenshot, width, height}
   */
  async captureScreen() {
    const response = await this.sendMessage({action: 'capture_screen'});
    if (!response || !response.success) {
      throw new Error(response?.error || 'Failed to capture screen');
    }
    return response;
  }

  /**
   * Inspect UI tree
   * @param {number} hwnd - Optional window handle
   * @returns {Promise<Object>} - UI tree data {success, uiTree}
   */
  async inspectUI(hwnd = null) {
    const message = {action: 'inspect_ui'};
    if (hwnd) {
      message.hwnd = hwnd;
    }
    
    const response = await this.sendMessage(message);
    if (!response || !response.success) {
      throw new Error(response?.error || 'Failed to inspect UI');
    }
    return response;
  }

  /**
   * Execute a single action
   * @param {Object} action - Action to execute {action, params}
   * @returns {Promise<Object>} - Execution result {success, error?}
   */
  async executeAction(action) {
    const message = {
      action: 'execute_action',
      params: action
    };
    
    const response = await this.sendMessage(message);
    if (!response || !response.success) {
      throw new Error(response?.error || `Failed to execute action: ${action.action}`);
    }
    return response;
  }

  /**
   * Execute multiple actions
   * @param {Array<Object>} actions - Array of actions to execute
   * @returns {Promise<Object>} - Execution result {success, executed_count, error?}
   */
  async executeActions(actions) {
    const message = {
      action: 'execute_actions',
      actions: actions
    };
    
    const response = await this.sendMessage(message);
    if (!response || !response.success) {
      throw new Error(response?.error || 'Failed to execute actions');
    }
    return response;
  }

  /**
   * Check if local LLM is available
   * @returns {Promise<Object>} - Availability info {success, available, error?}
   */
  async checkLocalLLM() {
    const response = await this.sendMessage({action: 'check_local_llm'});
    return response;
  }

  /**
   * Store an API key in the C++ service (Windows Credential Manager)
   */
  async storeApiKey(provider, apiKey) {
    const response = await this.sendMessage({
      action: 'store_api_key', provider, api_key: apiKey
    });
    if (!response || !response.success) {
      throw new Error(response?.error || 'Failed to store API key');
    }
    return response;
  }

  /**
   * Delete an API key
   */
  async deleteApiKey(provider) {
    return this.sendMessage({action: 'delete_api_key', provider});
  }

  /**
   * Get provider status (which have keys, which are available)
   */
  async getProviderStatus() {
    return this.sendMessage({action: 'get_provider_status'});
  }

  /**
   * Request AI actions (async — returns request_id)
   */
  async requestActions(provider, userRequest) {
    return this.sendMessage({
      action: 'get_actions', provider, user_request: userRequest
    });
  }

  /**
   * Poll for async request result
   */
  async pollRequest(requestId) {
    return this.sendMessage({action: 'poll', request_id: requestId});
  }

  /**
   * Cancel an async request
   */
  async cancelRequest(requestId) {
    return this.sendMessage({action: 'cancel', request_id: requestId});
  }

  /**
   * Poll until a request completes. Returns the final result.
   * @param {string} requestId
   * @param {number} intervalMs - polling interval (default 500ms)
   * @param {number} timeoutMs - max wait time (default 120000ms)
   */
  async pollUntilComplete(requestId, intervalMs = 500, timeoutMs = 120000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const result = await this.pollRequest(requestId);
      if (result.status === 'complete' || result.status === 'error' || result.status === 'cancelled') {
        return result;
      }
      await new Promise(r => setTimeout(r, intervalMs));
    }
    // Timeout — try to cancel
    await this.cancelRequest(requestId);
    throw new Error('AI request timed out');
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { NativeMessagingHelper };
}

