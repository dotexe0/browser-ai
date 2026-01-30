/**
 * AI Provider Manager
 *
 * Manages multiple AI providers and routes requests to the active provider.
 * Handles provider registration, selection, and configuration.
 */

const _keyEncrypt = {
  _cachedKey: null,

  async _getKey() {
    if (this._cachedKey) return this._cachedKey;
    const salt = new TextEncoder().encode('browser-ai-salt-v1');
    const baseKey = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(
        (navigator.userAgent || '') + (location.origin || '')
      ),
      'PBKDF2',
      false,
      ['deriveKey']
    );
    this._cachedKey = await crypto.subtle.deriveKey(
      { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
      baseKey,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
    return this._cachedKey;
  },

  async encrypt(plaintext) {
    const key = await this._getKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(plaintext);
    const ciphertext = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      encoded
    );
    const buf = new Uint8Array(iv.length + ciphertext.byteLength);
    buf.set(iv, 0);
    buf.set(new Uint8Array(ciphertext), iv.length);
    return btoa(String.fromCharCode(...buf));
  },

  async decrypt(stored) {
    try {
      const key = await this._getKey();
      const raw = Uint8Array.from(atob(stored), c => c.charCodeAt(0));
      const iv = raw.slice(0, 12);
      const ciphertext = raw.slice(12);
      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        ciphertext
      );
      return new TextDecoder().decode(decrypted);
    } catch {
      return stored;
    }
  }
};

class AIProviderManager {
  constructor() {
    /** @type {Map<string, AIProvider>} */
    this.providers = new Map();

    /** @type {AIProvider|null} */
    this.activeProvider = null;

    /** @type {Array<{role: string, content: any}>} */
    this.conversationHistory = [];

    this.ready = this.initialize();
  }

  /**
   * Initialize the manager and register available providers
   */
  async initialize() {
    // Register OpenAI provider (cloud, via backend proxy)
    const openaiProvider = new OpenAIProvider();
    this.registerProvider(openaiProvider);

    // Register Ollama provider (local, private, FREE!)
    const ollamaProvider = new OllamaProvider();
    this.registerProvider(ollamaProvider);

    // Register Anthropic provider (cloud, via backend proxy)
    const anthropicProvider = new AnthropicProvider();
    this.registerProvider(anthropicProvider);

    // Register Local LLM provider (via C++ Native Messaging service)
    const localProvider = new LocalLLMProvider();
    this.registerProvider(localProvider);

    // Load user's preferred provider from settings
    await this.loadUserPreference();
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
  async configureProvider(providerName, apiKey) {
    const provider = this.providers.get(providerName);

    if (!provider) {
      throw new Error(`Provider not found: ${providerName}`);
    }

    if (provider.requiresApiKey) {
      provider.setApiKey(apiKey);
      await this.saveApiKey(providerName, apiKey);
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
  async loadUserPreference() {
    try {
      const savedProvider = localStorage.getItem('ai_provider_preference');

      if (savedProvider && this.providers.has(savedProvider)) {
        this.activeProvider = this.providers.get(savedProvider);

        // Load API key if needed
        if (this.activeProvider.requiresApiKey) {
          const savedKey = await this.loadApiKey(savedProvider);
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
  async loadApiKey(providerName) {
    try {
      const stored = localStorage.getItem(`ai_provider_key_${providerName}`);
      if (!stored) return null;
      return await _keyEncrypt.decrypt(stored);
    } catch (error) {
      console.error('Error loading API key:', error);
      return null;
    }
  }

  /**
   * Save API key to localStorage (encrypted with AES-GCM)
   * @private
   */
  async saveApiKey(providerName, apiKey) {
    try {
      const encrypted = await _keyEncrypt.encrypt(apiKey);
      localStorage.setItem(`ai_provider_key_${providerName}`, encrypted);
    } catch (error) {
      console.error('Error saving API key:', error);
    }
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AIProviderManager };
}

