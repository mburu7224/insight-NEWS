/**
 * Israel News Module - Delivery API
 * Node.js Express server for serving Israeli news
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const { authenticateApiKey } = require('./middleware/auth');

// Import routes
const farmingRoutes = require('./routes/farming');
const techRoutes = require('./routes/tech');
const politicsRoutes = require('./routes/politics');
const hospitalityRoutes = require('./routes/hospitality');
const generalRoutes = require('./routes/general');

const app = express();
const PORT = process.env.PORT || 3000;
const REQUIRE_API_KEY = String(process.env.REQUIRE_API_KEY || 'false').toLowerCase() === 'true';
const maybeAuthenticateApiKey = REQUIRE_API_KEY
  ? authenticateApiKey
  : (req, res, next) => next();

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: { error: 'Too many requests, please try again later.' }
});
app.use('/api/', limiter);

// Routes (optionally protected with API key authentication)
app.use('/api/farming', maybeAuthenticateApiKey, farmingRoutes);
app.use('/api/tech', maybeAuthenticateApiKey, techRoutes);
app.use('/api/politics', maybeAuthenticateApiKey, politicsRoutes);
app.use('/api/hospitality', maybeAuthenticateApiKey, hospitalityRoutes);
app.use('/api/general', maybeAuthenticateApiKey, generalRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Real-time updates endpoint (SSE)
app.get('/api/stream', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  // Send initial connection message
  res.write(`data: ${JSON.stringify({ type: 'connected', timestamp: new Date().toISOString() })}\n\n`);
  
  // Send heartbeat every 30 seconds
  const heartbeat = setInterval(() => {
    res.write(`data: ${JSON.stringify({ type: 'heartbeat', timestamp: new Date().toISOString() })}\n\n`);
  }, 30000);
  
  // Clean up on close
  req.on('close', () => {
    clearInterval(heartbeat);
    res.end();
  });
});

// Notify clients of new articles (call this when new articles are added)
function broadcastNewArticle(article) {
  // In production, use WebSocket or a pub/sub system
  console.log('New article available:', article.title);
}

// API info endpoint
app.get('/api', (req, res) => {
  res.json({
    name: 'Israel News API',
    version: '1.0.0',
    endpoints: {
      farming: '/api/farming',
      tech: '/api/tech',
      politics: '/api/politics',
      hospitality: '/api/hospitality',
      general: '/api/general'
    }
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Start server
app.listen(PORT, () => {
  console.log(`Israel News API running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`API info: http://localhost:${PORT}/api`);
});

module.exports = app;
