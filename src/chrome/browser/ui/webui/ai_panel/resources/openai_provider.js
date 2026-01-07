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
 * OpenAI Provider implementation
 */
class OpenAIProvider extends AIProvider {
  constructor() {
    super('OpenAI GPT-4 Vision', true);
    this.apiEndpoint = 'https://api.openai.com/v1/chat/completions';
    this.model = 'gpt-4-vision-preview';
    this.temperature = 0.2; // Low temperature for more deterministic actions
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
   * Get actions from OpenAI GPT-4 Vision
   * @param {AIProviderParams} params 
   * @returns {Promise<Action[]>}
   */
  async getActions(params) {
    if (!this.isConfigured()) {
      throw new Error(this.getConfigError());
    }

    try {
      const response = await this.callOpenAI(params);
      return this.parseResponse(response);
    } catch (error) {
      console.error('OpenAI Provider error:', error);
      throw new Error(`OpenAI API error: ${error.message}`);
    }
  }

  /**
   * Call OpenAI API with screenshot and UI tree
   * @private
   */
  async callOpenAI(params) {
    const messages = [
      {
        role: 'system',
        content: AUTOMATION_SYSTEM_PROMPT
      },
      {
        role: 'user',
        content: [
          {
            type: 'text',
            text: `User Request: ${params.userRequest}\n\nUI Tree:\n${JSON.stringify(params.uiTree, null, 2)}`
          },
          {
            type: 'image_url',
            image_url: {
              url: `data:image/png;base64,${params.screenshot}`,
              detail: 'high' // High detail for better accuracy
            }
          }
        ]
      }
    ];

    // Add conversation history if provided
    if (params.conversationHistory && params.conversationHistory.length > 0) {
      messages.push(...params.conversationHistory);
    }

    const requestBody = {
      model: this.model,
      messages: messages,
      temperature: this.temperature,
      max_tokens: 4096,
      response_format: { type: 'json_object' }
    };

    const response = await fetch(this.apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Parse OpenAI response into actions array
   * @private
   */
  parseResponse(response) {
    try {
      const content = response.choices[0].message.content;
      const parsed = JSON.parse(content);
      
      // Handle both {"actions": [...]} and direct array formats
      const actions = parsed.actions || parsed;
      
      if (!Array.isArray(actions)) {
        throw new Error('Response is not an array of actions');
      }

      // Validate each action
      return actions.map(action => this.validateAction(action));
    } catch (error) {
      console.error('Failed to parse OpenAI response:', error);
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

