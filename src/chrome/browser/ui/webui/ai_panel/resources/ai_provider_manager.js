/**
 * AI Provider Manager
 *
 * Thin wrapper over NativeMessagingHelper for AI provider operations.
 * All AI logic (prompts, API calls, key storage) lives in the C++ service.
 */
class AIProviderManager {
  constructor(nativeMessaging) {
    this.native = nativeMessaging;
    this.activeProvider = 'ollama';
    this.providerStatus = {};
    this.ready = this.initialize();
  }

  async initialize() {
    try {
      const status = await this.native.getProviderStatus();
      if (status.success) {
        this.providerStatus = status.providers;
      }
      // Pick the best available provider
      const saved = localStorage.getItem('ai_provider_preference');
      if (saved && this.providerStatus[saved]) {
        this.activeProvider = saved;
      }
    } catch (e) {
      console.error('Failed to initialize provider manager:', e);
    }
  }

  getActiveProvider() {
    return this.activeProvider;
  }

  setActiveProvider(provider) {
    this.activeProvider = provider;
    localStorage.setItem('ai_provider_preference', provider);
  }

  getProviderStatus() {
    return this.providerStatus;
  }

  async refreshStatus() {
    try {
      const status = await this.native.getProviderStatus();
      if (status.success) {
        this.providerStatus = status.providers;
      }
    } catch (e) {
      console.error('Failed to refresh provider status:', e);
    }
    return this.providerStatus;
  }

  async storeApiKey(provider, apiKey) {
    await this.native.storeApiKey(provider, apiKey);
    await this.refreshStatus();
  }

  async deleteApiKey(provider) {
    await this.native.deleteApiKey(provider);
    await this.refreshStatus();
  }

  /**
   * Request AI actions. Returns actions array.
   * Handles async polling internally.
   */
  async getActions(userRequest) {
    const { request_id } = await this.native.requestActions(
      this.activeProvider, userRequest
    );
    return this.native.pollUntilComplete(request_id);
  }

  async cancelRequest(requestId) {
    return this.native.cancelRequest(requestId);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AIProviderManager };
}
