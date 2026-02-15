/**
 * Israel News Module - API Authentication Middleware
 * Supports API Key and JWT authentication
 */

const crypto = require('crypto');

// In-memory API key store (in production, use a database)
const apiKeys = new Map();

// Initialize default API keys from environment
function initializeApiKeys() {
  const envKeys = process.env.API_KEYS || '';
  const defaultKeys = envKeys ? envKeys.split(',') : [];
  
  defaultKeys.forEach((key, index) => {
    const trimmedKey = key.trim();
    if (!trimmedKey) {
      return;
    }
    const keyName = `key_${index + 1}`;
    apiKeys.set(trimmedKey, {
      name: keyName,
      createdAt: new Date(),
      rateLimit: 1000, // requests per hour
      requestsThisHour: 0,
      lastReset: Date.now()
    });
  });
  
  // Add a default development key if none exist and we're not in production
  if (apiKeys.size === 0 && process.env.NODE_ENV !== 'production') {
    const devKey = crypto.randomBytes(32).toString('hex');
    apiKeys.set(devKey, {
      name: 'development',
      createdAt: new Date(),
      rateLimit: 100,
      requestsThisHour: 0,
      lastReset: Date.now(),
      isDev: true
    });
    console.warn('No API_KEYS configured. Generated a development API key.');
  }
}

initializeApiKeys();

/**
 * API Key authentication middleware
 * Pass API key in header: x-api-key
 */
function authenticateApiKey(req, res, next) {
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey) {
    return res.status(401).json({
      success: false,
      error: 'API key required. Include x-api-key header.'
    });
  }
  
  const keyData = apiKeys.get(apiKey);
  
  if (!keyData) {
    return res.status(403).json({
      success: false,
      error: 'Invalid API key'
    });
  }
  
  // Check rate limit (reset every hour)
  const now = Date.now();
  if (now - keyData.lastReset > 3600000) {
    keyData.requestsThisHour = 0;
    keyData.lastReset = now;
  }
  
  if (keyData.requestsThisHour >= keyData.rateLimit) {
    return res.status(429).json({
      success: false,
      error: 'Rate limit exceeded. Try again later.',
      resetIn: Math.ceil((3600000 - (now - keyData.lastReset)) / 60000) + ' minutes'
    });
  }
  
  // Update request count
  keyData.requestsThisHour++;
  
  // Attach key data to request
  req.apiKey = keyData;
  next();
}

/**
 * JWT-style token authentication (optional)
 */
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN
  
  if (!token) {
    return res.status(401).json({
      success: false,
      error: 'Access token required'
    });
  }
  
  // In production, verify JWT token here
  // For now, accept any non-empty token
  if (token.length < 10) {
    return res.status(403).json({
      success: false,
      error: 'Invalid token'
    });
  }
  
  req.user = { token };
  next();
}

/**
 * Generate a new API key
 * @param {string} name - Name for the API key
 * @param {number} rateLimit - Requests per hour
 */
function generateApiKey(name, rateLimit = 100) {
  const key = crypto.randomBytes(32).toString('hex');
  
  apiKeys.set(key, {
    name,
    createdAt: new Date(),
    rateLimit,
    requestsThisHour: 0,
    lastReset: Date.now()
  });
  
  return key;
}

/**
 * Revoke an API key
 * @param {string} key - API key to revoke
 */
function revokeApiKey(key) {
  return apiKeys.delete(key);
}

/**
 * Get API key info
 * @param {string} key - API key
 */
function getApiKeyInfo(key) {
  const keyData = apiKeys.get(key);
  if (!keyData) return null;
  
  return {
    name: keyData.name,
    createdAt: keyData.createdAt,
    rateLimit: keyData.rateLimit,
    requestsRemaining: keyData.rateLimit - keyData.requestsThisHour
  };
}

module.exports = {
  authenticateApiKey,
  authenticateToken,
  generateApiKey,
  revokeApiKey,
  getApiKeyInfo,
  apiKeys
};
