/**
 * Ollama Local LLM Provider
 * 
 * Uses Ollama for local, private AI inference.
 * 
 * Benefits:
 * - 100% private (never leaves your machine)
 * - No API key required
 * - Free to use
 * - Works offline
 * 
 * Setup:
 * 1. Install Ollama from https://ollama.ai
 * 2. Run: ollama pull llava (vision model)
 * 3. Start backend server
 * 4. Ready to use!
 */

class OllamaProvider extends AIProvider {
  constructor() {
    super('Ollama (Local & Private)', false); // No API key needed!
    this.backendEndpoint = 'http://localhost:5000/api/get-actions';
    this.providerId = 'ollama';
    this.model = 'llava'; // Vision-capable model
  }

  getCapabilities() {
    return {
      supportsVision: true,
      supportsStreaming: false,
      maxImageSize: 10 * 1024 * 1024, // 10MB (smaller for local)
      contextWindow: 4096, // Smaller than cloud models
      privacy: 'full', // Everything stays local!
      cost: 0 // FREE!
    };
  }

  /**
   * Check if Ollama is running and available
   */
  async isConfigured() {
    try {
      const response = await fetch('http://localhost:11434/api/tags');
      const data = await response.json();
      
      // Check if llava model is installed
      const hasLlava = data.models?.some(m => m.name.includes('llava'));
      
      if (!hasLlava) {
        console.warn('Ollama is running but llava model not found. Run: ollama pull llava');
        return false;
      }
      
      return true;
    } catch (error) {
      console.error('Ollama not available:', error);
      return false;
    }
  }

  /**
   * Get actions from Ollama (via backend proxy)
   * @param {AIProviderParams} params 
   * @returns {Promise<Action[]>}
   */
  async getActions(params) {
    const configured = await this.isConfigured();
    if (!configured) {
      throw new Error('Ollama not running. Install from https://ollama.ai and run: ollama pull llava');
    }

    try {
      const response = await this.callBackend(params);
      return this.parseResponse(response);
    } catch (error) {
      console.error('Ollama Provider error:', error);
      throw new Error(`Ollama error: ${error.message}`);
    }
  }

  /**
   * Call backend proxy with screenshot and UI tree
   * @private
   */
  async callBackend(params) {
    const requestBody = {
      provider: this.providerId,
      screenshot: params.screenshot,
      ui_tree: params.uiTree,
      user_request: params.userRequest
    };

    const response = await fetch(this.backendEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Parse backend response into actions array
   * @private
   */
  parseResponse(response) {
    if (response.error) {
      throw new Error(response.error);
    }

    if (!response.success || !Array.isArray(response.actions)) {
      throw new Error('Invalid response from Ollama');
    }

    // Validate each action
    return response.actions.map(action => this.validateAction(action));
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

    // Local models might be less confident
    if (typeof action.confidence !== 'number') {
      action.confidence = 0.7; // Slightly lower default for local models
    }

    return action;
  }

  /**
   * Estimate cost - always free for local models!
   * @returns {number} Cost in USD
   */
  estimateCost(params) {
    return 0; // FREE! 🎉
  }

  /**
   * Get a friendly status message
   */
  async getStatusMessage() {
    const configured = await this.isConfigured();
    
    if (configured) {
      return '✅ Ollama running locally (private & free)';
    } else {
      return '❌ Ollama not found. Install from https://ollama.ai';
    }
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { OllamaProvider };
}

