/**
 * Anthropic Claude Provider
 *
 * Uses Anthropic's Claude API for desktop automation via backend proxy.
 */

class AnthropicProvider extends AIProvider {
  constructor() {
    super('Anthropic Claude', false);
    this.backendEndpoint = 'http://localhost:5000/api/get-actions';
    this.providerId = 'anthropic';
  }

  getCapabilities() {
    return {
      supportsVision: true,
      supportsStreaming: false,
      maxImageSize: 20 * 1024 * 1024,
      contextWindow: 200000
    };
  }

  async isConfigured() {
    try {
      const response = await fetch('http://localhost:5000/api/health');
      const data = await response.json();
      return data.providers.anthropic === true;
    } catch (error) {
      return false;
    }
  }

  async getActions(params) {
    const configured = await this.isConfigured();
    if (!configured) {
      throw new Error('Anthropic not configured. Set ANTHROPIC_API_KEY in backend .env file.');
    }

    const response = await this.callBackend(params);
    return this.parseResponse(response);
  }

  async callBackend(params) {
    const requestBody = {
      provider: this.providerId,
      screenshot: params.screenshot,
      ui_tree: params.uiTree,
      user_request: params.userRequest
    };

    const response = await fetch(this.backendEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return await response.json();
  }

  parseResponse(response) {
    if (response.error) throw new Error(response.error);
    if (!response.success || !Array.isArray(response.actions)) {
      throw new Error('Invalid response from Anthropic');
    }
    return response.actions.map(action => this.validateAction(action));
  }

  validateAction(action) {
    const validActions = ['click', 'type', 'scroll', 'press_keys', 'wait'];
    if (!action.action || !validActions.includes(action.action)) {
      throw new Error(`Invalid action type: ${action.action}`);
    }
    if (!action.params || typeof action.params !== 'object') {
      throw new Error(`Action missing params: ${JSON.stringify(action)}`);
    }
    if (typeof action.confidence !== 'number') {
      action.confidence = 0.85;
    }
    return action;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AnthropicProvider };
}
