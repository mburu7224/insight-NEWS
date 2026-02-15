/**
 * Farming News API Route
 */

const express = require('express');
const router = express.Router();
const { getArticlesByCategory } = require('../db');

// Demo/Mock data for Farming category
const DEMO_FARMING_ARTICLES = [
  {
    id: 2,
    title: 'New Agricultural Technology Revolutionizes Farming in Israel',
    description: 'Israeli farmers adopt drone technology and AI to increase crop yields by 30%.',
    url: 'https://example.com/israel-agtech',
    image_url: 'https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=800',
    published_at: new Date(Date.now() - 3600000).toISOString(),
    source: 'Israel21c',
    category_name: 'farming',
    summary: ['Drone technology adoption', '30% increase in crop yields', 'AI-powered irrigation systems'],
    sentiment: 'positive',
    importance: 'medium'
  },
  {
    id: 8,
    title: 'Israeli Dates Reach Global Markets',
    description: 'Premium Israeli dates in high demand across Europe and Asia.',
    url: 'https://example.com/israel-dates',
    image_url: 'https://images.unsplash.com/photo-1595188882354-274e1d746562?w=800',
    published_at: new Date(Date.now() - 7200000).toISOString(),
    source: 'Agricultural News',
    category_name: 'farming',
    summary: ['Premium date exports', 'Growing demand in Asia', 'Sustainable farming practices'],
    sentiment: 'positive',
    importance: 'medium'
  },
  {
    id: 9,
    title: 'Desert Farming Innovation in the Negev',
    description: 'New techniques allow farming in arid regions of southern Israel.',
    url: 'https://example.com/negev-farming',
    image_url: 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800',
    published_at: new Date(Date.now() - 10800000).toISOString(),
    source: 'Farm Weekly',
    category_name: 'farming',
    summary: ['Desert agriculture breakthrough', 'New irrigation techniques', 'Negev development'],
    sentiment: 'positive',
    importance: 'medium'
  }
];

// Get farming news
router.get('/', async (req, res) => {
  try {
    const parsedLimit = Number.parseInt(req.query.limit, 10);
    const parsedPage = Number.parseInt(req.query.page, 10);
    const limit = Number.isFinite(parsedLimit) && parsedLimit > 0 ? Math.min(parsedLimit, 100) : 20;
    const page = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;
    const offset = (page - 1) * limit;
    
    let articles;
    try {
      articles = await getArticlesByCategory('farming', limit, offset);
    } catch (dbError) {
      console.warn('Database unavailable, using demo data');
      articles = DEMO_FARMING_ARTICLES;
    }
    
    if (!articles || articles.length === 0) {
      articles = DEMO_FARMING_ARTICLES.slice(0, limit);
    }
    
    res.json({
      success: true,
      category: 'farming',
      count: articles.length,
      page,
      limit,
      data: articles
    });
  } catch (error) {
    console.error('Error fetching farming news:', error);
    res.json({
      success: true,
      category: 'farming',
      count: DEMO_FARMING_ARTICLES.length,
      page: 1,
      limit: 20,
      data: DEMO_FARMING_ARTICLES,
      demo: true
    });
  }
});

module.exports = router;
