/**
 * AI Provider Manager
 * 
 * Manages multiple AI providers and routes requests to the active provider.
 * Handles provider registration, selection, and configuration.
 */

class AIProviderManager {
  constructor() {
    /** @type {Map<string, AIProvider>} */
    this.providers = new Map();
    
    /** @type {AIProvider|null} */
    this.activeProvider = null;
    
    /** @type {Array<{role: string, content: any}>} */
    this.conversationHistory = [];
    
    this.initialize();
  }

  /**
   * Initialize the manager and register available providers
   */
  initialize() {
    // Register OpenAI provider (cloud, via backend proxy)
    const openaiProvider = new OpenAIProvider();
    this.registerProvider(openaiProvider);
    
    // Register Ollama provider (local, private, FREE!)
    const ollamaProvider = new OllamaProvider();
    this.registerProvider(ollamaProvider);
    
    // Register Local LLM provider (via C++ Native Messaging service)
    const localProvider = new LocalLLMProvider();
    this.registerProvider(localProvider);
    
    // TODO: Register Anthropic MCP provider when implemented
    // const mcpProvider = new AnthropicMCPProvider();
    // this.registerProvider(mcpProvider);
    
    // Load user's preferred provider from settings
    this.loadUserPreference();
  }

  /**
   * Register a new provider
   * @param {AIProvider} provider 
   */
  registerProvider(provider) {
    if (!(provider instanceof AIProvider)) {
      throw new Error('Provider must extend AIProvider class');
    }
    
    this.providers.set(provider.name, provider);
    console.log(`Registered AI provider: ${provider.name}`);
  }

  /**
   * Set the active provider by name
   * @param {string} providerName 
   * @returns {boolean} True if successful
   */
  setActiveProvider(providerName) {
    const provider = this.providers.get(providerName);
    
    if (!provider) {
      console.error(`Provider not found: ${providerName}`);
      return false;
    }
    
    this.activeProvider = provider;
    this.saveUserPreference(providerName);
    
    console.log(`Active provider set to: ${providerName}`);
    return true;
  }

  /**
   * Get the currently active provider
   * @returns {AIProvider|null}
   */
  getActiveProvider() {
    return this.activeProvider;
  }

  /**
   * Get a specific provider by name
   * @param {string} providerName 
   * @returns {AIProvider|null}
   */
  getProvider(providerName) {
    return this.providers.get(providerName) || null;
  }

  /**
   * Get list of all available providers
   * @returns {Array<{name: string, requiresApiKey: boolean, supportsVision: boolean, configured: boolean}>}
   */
  getAvailableProviders() {
    return Array.from(this.providers.values()).map(provider => ({
      name: provider.name,
      requiresApiKey: provider.requiresApiKey,
      supportsVision: provider.supportsVision,
      configured: provider.isConfigured()
    }));
  }

  /**
   * Configure a provider's API key
   * @param {string} providerName 
   * @param {string} apiKey 
   */
  configureProvider(providerName, apiKey) {
    const provider = this.providers.get(providerName);
    
    if (!provider) {
      throw new Error(`Provider not found: ${providerName}`);
    }
    
    if (provider.requiresApiKey) {
      provider.setApiKey(apiKey);
      this.saveApiKey(providerName, apiKey);
      console.log(`Configured API key for: ${providerName}`);
    }
  }

  /**
   * Main method: Get automation actions from active provider
   * @param {AIProviderParams} params 
   * @returns {Promise<Action[]>}
   */
  async getActions(params) {
    if (!this.activeProvider) {
      throw new Error('No active AI provider selected');
    }
    
    if (!this.activeProvider.isConfigured()) {
      throw new Error(this.activeProvider.getConfigError());
    }
    
    // Add conversation history to params
    const enrichedParams = {
      ...params,
      conversationHistory: this.conversationHistory
    };
    
    try {
      const actions = await this.activeProvider.getActions(enrichedParams);
      
      // Update conversation history
      this.updateConversationHistory(params.userRequest, actions);
      
      return actions;
    } catch (error) {
      console.error('Error getting actions from provider:', error);
      throw error;
    }
  }

  /**
   * Update conversation history for context
   * @private
   */
  updateConversationHistory(userRequest, actions) {
    // Add user request
    this.conversationHistory.push({
      role: 'user',
      content: userRequest
    });
    
    // Add assistant response (actions)
    this.conversationHistory.push({
      role: 'assistant',
      content: JSON.stringify({ actions })
    });
    
    // Keep only last 10 exchanges (20 messages)
    if (this.conversationHistory.length > 20) {
      this.conversationHistory = this.conversationHistory.slice(-20);
    }
  }

  /**
   * Clear conversation history
   */
  clearConversationHistory() {
    this.conversationHistory = [];
    console.log('Conversation history cleared');
  }

  /**
   * Load user's preferred provider from localStorage
   * @private
   */
  loadUserPreference() {
    try {
      const savedProvider = localStorage.getItem('ai_provider_preference');
      
      if (savedProvider && this.providers.has(savedProvider)) {
        this.activeProvider = this.providers.get(savedProvider);
        
        // Load API key if needed
        if (this.activeProvider.requiresApiKey) {
          const savedKey = this.loadApiKey(savedProvider);
          if (savedKey) {
            this.activeProvider.setApiKey(savedKey);
          }
        }
        
        console.log(`Loaded preferred provider: ${savedProvider}`);
      } else {
        // Default to first available provider
        const firstProvider = Array.from(this.providers.values())[0];
        this.activeProvider = firstProvider;
        console.log(`Using default provider: ${firstProvider.name}`);
      }
    } catch (error) {
      console.error('Error loading user preference:', error);
      // Fall back to first provider
      this.activeProvider = Array.from(this.providers.values())[0];
    }
  }

  /**
   * Save user's provider preference to localStorage
   * @private
   */
  saveUserPreference(providerName) {
    try {
      localStorage.setItem('ai_provider_preference', providerName);
    } catch (error) {
      console.error('Error saving user preference:', error);
    }
  }

  /**
   * Load API key from localStorage (encrypted in production)
   * @private
   */
  loadApiKey(providerName) {
    try {
      // In production, this should be encrypted
      return localStorage.getItem(`ai_provider_key_${providerName}`);
    } catch (error) {
      console.error('Error loading API key:', error);
      return null;
    }
  }

  /**
   * Save API key to localStorage (should be encrypted in production)
   * @private
   */
  saveApiKey(providerName, apiKey) {
    try {
      // WARNING: In production, encrypt this!
      // For now, storing in localStorage for development
      localStorage.setItem(`ai_provider_key_${providerName}`, apiKey);
    } catch (error) {
      console.error('Error saving API key:', error);
    }
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AIProviderManager };
}

