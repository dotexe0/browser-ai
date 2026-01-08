/**
 * OpenAI GPT-4 Vision Provider
 * 
 * Uses OpenAI's GPT-4 Vision API for desktop automation.
 * Sends screenshot + UI tree to GPT-4V and receives automation actions.
 */

/**
 * System prompt for desktop automation
 */
const AUTOMATION_SYSTEM_PROMPT = `You are a desktop automation assistant. You can:
1. See the screen (provided as image)
2. Inspect UI elements (provided as JSON tree with element positions and properties)
3. Perform actions: click, type, scroll, press keys, wait

When given a user request, analyze the screen and UI tree, then return a JSON array of actions.

Action format:
[
  {"action": "click", "params": {"x": 100, "y": 200, "button": "left"}},
  {"action": "type", "params": {"text": "Hello World"}},
  {"action": "press_keys", "params": {"keys": ["ctrl", "s"]}},
  {"action": "scroll", "params": {"delta": -3, "x": 500, "y": 300}},
  {"action": "wait", "params": {"ms": 1000}}
]

Important guidelines:
- Be precise with coordinates - verify elements exist in UI tree
- Use element bounds from UI tree for accurate clicking
- Break complex tasks into sequential actions
- Add wait actions between steps that need time to complete
- Return ONLY a valid JSON array, no explanatory text

Respond with a JSON object containing an "actions" array.`;

/**
 * OpenAI Provider implementation (via secure backend proxy)
 * 
 * Note: This provider routes through backend/server.py to keep API keys secure.
 * API keys are NEVER exposed to the browser.
 */
class OpenAIProvider extends AIProvider {
  constructor() {
    super('OpenAI GPT-4 Vision', false); // No API key needed in browser!
    this.backendEndpoint = 'http://localhost:5000/api/get-actions';
    this.providerId = 'openai';
    this.model = 'gpt-4-vision-preview';
  }

  getCapabilities() {
    return {
      supportsVision: true,
      supportsStreaming: false,
      maxImageSize: 20 * 1024 * 1024, // 20MB
      contextWindow: 128000 // tokens
    };
  }

  /**
   * Check if provider is configured (backend has API key)
   */
  async isConfigured() {
    try {
      const response = await fetch('http://localhost:5000/api/health');
      const data = await response.json();
      return data.providers.openai === true;
    } catch (error) {
      console.error('Failed to check OpenAI configuration:', error);
      return false;
    }
  }

  /**
   * Get actions from OpenAI GPT-4 Vision (via backend proxy)
   * @param {AIProviderParams} params 
   * @returns {Promise<Action[]>}
   */
  async getActions(params) {
    const configured = await this.isConfigured();
    if (!configured) {
      throw new Error('OpenAI provider not configured. Start backend server with OPENAI_API_KEY.');
    }

    try {
      const response = await this.callBackend(params);
      return this.parseResponse(response);
    } catch (error) {
      console.error('OpenAI Provider error:', error);
      throw new Error(`OpenAI error: ${error.message}`);
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
      throw new Error('Invalid response from backend');
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

    // Add default confidence if not provided
    if (typeof action.confidence !== 'number') {
      action.confidence = 0.8; // Default confidence
    }

    return action;
  }

  /**
   * Estimate cost for a request (approximate)
   * @param {AIProviderParams} params 
   * @returns {number} Estimated cost in USD
   */
  estimateCost(params) {
    // GPT-4 Vision pricing (approximate):
    // Input: $0.01/1K tokens, Images: $0.01275 per image
    // Output: $0.03/1K tokens
    
    const imageCost = 0.01275;
    const inputTokens = JSON.stringify(params.uiTree).length / 4; // Rough estimate
    const inputCost = (inputTokens / 1000) * 0.01;
    const outputCost = (500 / 1000) * 0.03; // Estimate 500 tokens output
    
    return imageCost + inputCost + outputCost;
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { OpenAIProvider };
}

