/**
 * Hospitality News API Route
 */

const express = require('express');
const router = express.Router();
const { getArticlesByCategory } = require('../db');

// Demo/Mock data for Hospitality category
const DEMO_HOSPITALITY_ARTICLES = [
  {
    id: 3,
    title: 'Israel Announces New Tourism Initiatives for 2025',
    description: 'Government unveils plans to attract 10 million tourists with new hotels and attractions.',
    url: 'https://example.com/israel-tourism',
    image_url: 'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=800',
    published_at: new Date(Date.now() - 7200000).toISOString(),
    source: 'Globes',
    category_name: 'hospitality',
    summary: ['New tourism strategy', 'Target: 10 million visitors', 'New hotel developments'],
    sentiment: 'positive',
    importance: 'medium'
  },
  {
    id: 12,
    title: 'Tel Aviv Named Top Culinary Destination',
    description: 'International travel magazine praises Tel Aviv restaurant scene.',
    url: 'https://example.com/tel-aviv-food',
    image_url: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800',
    published_at: new Date(Date.now() - 14400000).toISOString(),
    source: 'Travel Weekly',
    category_name: 'hospitality',
    summary: ['Culinary destination recognition', 'Diverse restaurant scene', 'Food tourism growth'],
    sentiment: 'positive',
    importance: 'medium'
  },
  {
    id: 13,
    title: 'Luxury Hotels Open in Jerusalem',
    description: 'New five-star hotels bring international standards to Jerusalem.',
    url: 'https://example.com/jerusalem-hotels',
    image_url: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800',
    published_at: new Date(Date.now() - 21600000).toISOString(),
    source: 'Hospitality News',
    category_name: 'hospitality',
    summary: ['New luxury hotels', 'Jerusalem tourism boost', 'International brands'],
    sentiment: 'positive',
    importance: 'medium'
  }
];

// Get hospitality news
router.get('/', async (req, res) => {
  try {
    const parsedLimit = Number.parseInt(req.query.limit, 10);
    const parsedPage = Number.parseInt(req.query.page, 10);
    const limit = Number.isFinite(parsedLimit) && parsedLimit > 0 ? Math.min(parsedLimit, 100) : 20;
    const page = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;
    const offset = (page - 1) * limit;
    
    let articles;
    try {
      articles = await getArticlesByCategory('hospitality', limit, offset);
    } catch (dbError) {
      console.warn('Database unavailable, using demo data');
      articles = DEMO_HOSPITALITY_ARTICLES;
    }
    
    if (!articles || articles.length === 0) {
      articles = DEMO_HOSPITALITY_ARTICLES.slice(0, limit);
    }
    
    res.json({
      success: true,
      category: 'hospitality',
      count: articles.length,
      page,
      limit,
      data: articles
    });
  } catch (error) {
    console.error('Error fetching hospitality news:', error);
    res.json({
      success: true,
      category: 'hospitality',
      count: DEMO_HOSPITALITY_ARTICLES.length,
      page: 1,
      limit: 20,
      data: DEMO_HOSPITALITY_ARTICLES,
      demo: true
    });
  }
});

module.exports = router;
