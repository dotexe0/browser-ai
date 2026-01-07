/**
 * AI Provider Interface
 * 
 * Defines the contract that all AI providers must implement.
 * This allows swapping between OpenAI, Local LLMs, Anthropic MCP, etc.
 */

/**
 * @typedef {Object} Action
 * @property {'click'|'type'|'scroll'|'press_keys'|'wait'} action - The action type
 * @property {Object} params - Action-specific parameters
 * @property {number} [confidence] - AI confidence score (0-1)
 */

/**
 * @typedef {Object} AIProviderParams
 * @property {string} screenshot - Base64 encoded screenshot
 * @property {Object} uiTree - JSON UI tree from UIAutomation
 * @property {string} userRequest - Natural language user request
 * @property {Array} [conversationHistory] - Optional conversation context
 */

/**
 * @typedef {Object} ProviderCapabilities
 * @property {boolean} supportsVision - Can process images
 * @property {boolean} supportsStreaming - Can stream responses
 * @property {number} maxImageSize - Max image size in bytes
 * @property {number} contextWindow - Token context window
 */

/**
 * Base class for AI Providers
 * All providers must extend this class and implement getActions()
 */
class AIProvider {
  /**
   * @param {string} name - Provider display name
   * @param {boolean} requiresApiKey - Whether provider needs API key
   */
  constructor(name, requiresApiKey = false) {
    this.name = name;
    this.requiresApiKey = requiresApiKey;
    this.supportsVision = true;
    this.apiKey = null;
  }

  /**
   * Set the API key for this provider
   * @param {string} key - API key
   */
  setApiKey(key) {
    this.apiKey = key;
  }

  /**
   * Get provider capabilities
   * @returns {ProviderCapabilities}
   */
  getCapabilities() {
    return {
      supportsVision: this.supportsVision,
      supportsStreaming: false,
      maxImageSize: 20 * 1024 * 1024, // 20MB default
      contextWindow: 128000 // tokens
    };
  }

  /**
   * Main method: Given context, return automation actions
   * Must be implemented by subclasses
   * 
   * @param {AIProviderParams} params - Request parameters
   * @returns {Promise<Action[]>} Array of actions to execute
   */
  async getActions(params) {
    throw new Error('getActions() must be implemented by subclass');
  }

  /**
   * Validate that the provider is properly configured
   * @returns {boolean} True if ready to use
   */
  isConfigured() {
    if (this.requiresApiKey && !this.apiKey) {
      return false;
    }
    return true;
  }

  /**
   * Get configuration error message if not configured
   * @returns {string|null} Error message or null if configured
   */
  getConfigError() {
    if (this.requiresApiKey && !this.apiKey) {
      return `${this.name} requires an API key. Please configure it in settings.`;
    }
    return null;
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AIProvider };
}

