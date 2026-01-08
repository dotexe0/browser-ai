/**
 * Local LLM Provider
 * 
 * Routes AI inference requests to local LLM running via the automation service.
 * Provides privacy-focused alternative to cloud APIs.
 * 
 * Requires:
 * - Automation service with local_ai_proxy module
 * - Local inference server (Ollama, llama.cpp, vLLM)
 * - Vision-capable model (LLaVA, CogAgent, etc.)
 */

class LocalLLMProvider extends AIProvider {
  constructor() {
    super('Local LLM (Privacy)', false);
    this.supportsVision = true;
    this.available = false;
    this.modelInfo = null;
  }

  getCapabilities() {
    return {
      supportsVision: true,
      supportsStreaming: false,
      maxImageSize: 10 * 1024 * 1024, // 10MB (local models may have limits)
      contextWindow: this.modelInfo?.contextWindow || 4096
    };
  }

  /**
   * Check if local LLM is available
   * @returns {Promise<boolean>}
   */
  async checkAvailability() {
    try {
      // Query automation service to check if local LLM is running
      const response = await this.sendNativeMessage({
        action: 'check_local_llm'
      });
      
      this.available = response.available || false;
      this.modelInfo = response.modelInfo || null;
      
      return this.available;
    } catch (error) {
      console.warn('Local LLM not available:', error);
      this.available = false;
      return false;
    }
  }

  /**
   * Get actions from local LLM
   * @param {AIProviderParams} params 
   * @returns {Promise<Action[]>}
   */
  async getActions(params) {
    // Check availability first
    if (!this.available) {
      await this.checkAvailability();
    }
    
    if (!this.available) {
      throw new Error('Local LLM is not available. Please ensure:\n' +
        '1. Automation service is running\n' +
        '2. Local inference server is running (Ollama/llama.cpp)\n' +
        '3. A vision-capable model is loaded');
    }
    
    try {
      // Send request to automation service, which proxies to local LLM
      const response = await this.sendNativeMessage({
        action: 'ai_query_local',
        screenshot: params.screenshot,
        ui_tree: params.uiTree,
        user_request: params.userRequest,
        conversation_history: params.conversationHistory
      });
      
      if (!response.success) {
        throw new Error(response.error || 'Local LLM request failed');
      }
      
      return this.parseResponse(response);
    } catch (error) {
      console.error('Local LLM Provider error:', error);
      throw new Error(`Local LLM error: ${error.message}`);
    }
  }

  /**
   * Send message to automation service via Native Messaging
   * @private
   * @returns {Promise<any>}
   */
  async sendNativeMessage(message) {
    return new Promise((resolve, reject) => {
      // Check if running in browser context
      if (typeof chrome === 'undefined' || !chrome.runtime) {
        console.warn('Chrome runtime not available, using stub');
        // Fallback for testing outside of Chrome
        setTimeout(() => {
          if (message.action === 'check_local_llm') {
            resolve({
              available: false,
              error: 'Chrome runtime not available'
            });
          } else {
            reject(new Error('Chrome runtime not available'));
          }
        }, 100);
        return;
      }
      
      // Send message to native automation service
      chrome.runtime.sendNativeMessage(
        'com.browser_ai.automation',
        message,
        response => {
          // Check for errors
          if (chrome.runtime.lastError) {
            console.error('Native messaging error:', chrome.runtime.lastError);
            reject(new Error(chrome.runtime.lastError.message));
            return;
          }
          
          // Check if response is valid
          if (!response) {
            reject(new Error('No response from automation service'));
            return;
          }
          
          resolve(response);
        }
      );
    });
  }

  /**
   * Parse response from local LLM
   * @private
   */
  parseResponse(response) {
    try {
      const actions = response.actions;
      
      if (!Array.isArray(actions)) {
        throw new Error('Response is not an array of actions');
      }
      
      // Validate each action
      return actions.map(action => this.validateAction(action));
    } catch (error) {
      console.error('Failed to parse local LLM response:', error);
      throw new Error(`Invalid response format: ${error.message}`);
    }
  }

  /**
   * Validate and normalize an action
   * @private
   */
  validateAction(action) {
    const validActions = ['click', 'type', 'scroll', 'press_keys', 'wait'];
    
    if (!action.action || !validActions.includes(action.action)) {
      throw new Error(`Invalid action type: ${action.action}`);
    }
    
    if (!action.params || typeof action.params !== 'object') {
      throw new Error(`Action missing params: ${JSON.stringify(action)}`);
    }
    
    // Add default confidence if not provided
    if (typeof action.confidence !== 'number') {
      action.confidence = 0.7; // Local LLMs typically less confident
    }
    
    return action;
  }

  /**
   * Check if provider is configured (always true for local LLM)
   * @returns {boolean}
   */
  isConfigured() {
    return true; // No API key needed, but may not be available
  }

  /**
   * Get configuration error if not available
   * @returns {string|null}
   */
  getConfigError() {
    if (!this.available) {
      return 'Local LLM is not available. Please set up local inference server.';
    }
    return null;
  }

  /**
   * Get model information
   * @returns {Object|null}
   */
  getModelInfo() {
    return this.modelInfo;
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { LocalLLMProvider };
}

