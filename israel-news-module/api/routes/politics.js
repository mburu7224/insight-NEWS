/**
 * Politics News API Route
 */

const express = require('express');
const router = express.Router();
const { getArticlesByCategory } = require('../db');

// Demo/Mock data for Politics category
const DEMO_POLITICS_ARTICLES = [
  {
    id: 4,
    title: 'Israeli Parliament Passes New Economic Reform Bill',
    description: 'Knesset approves landmark legislation aimed at boosting economic growth and innovation.',
    url: 'https://example.com/israel-politics',
    image_url: 'https://images.unsplash.com/photo-1572949645079-64129567888b?w=800',
    published_at: new Date(Date.now() - 10800000).toISOString(),
    source: 'The Times of Israel',
    category_name: 'politics',
    summary: ['Economic reform passed', 'Focus on innovation sector', 'Bipartisan support'],
    sentiment: 'neutral',
    importance: 'high'
  },
  {
    id: 10,
    title: 'New Trade Agreements Signed with EU',
    description: 'Israel and European Union finalize new trade deal worth billions.',
    url: 'https://example.com/israel-eu-trade',
    image_url: 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800',
    published_at: new Date(Date.now() - 18000000).toISOString(),
    source: 'Jerusalem Post',
    category_name: 'politics',
    summary: ['EU trade agreement', 'Billions in trade value', 'Strengthened relations'],
    sentiment: 'positive',
    importance: 'high'
  },
  {
    id: 11,
    title: 'Government Announces Infrastructure Investment Plan',
    description: 'Major investment in transportation and digital infrastructure announced.',
    url: 'https://example.com/israel-infrastructure',
    image_url: 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800',
    published_at: new Date(Date.now() - 21600000).toISOString(),
    source: 'Haaretz',
    category_name: 'politics',
    summary: ['Infrastructure investment', 'Transportation projects', 'Digital transformation'],
    sentiment: 'positive',
    importance: 'medium'
  }
];

// Get politics news
router.get('/', async (req, res) => {
  try {
    const parsedLimit = Number.parseInt(req.query.limit, 10);
    const parsedPage = Number.parseInt(req.query.page, 10);
    const limit = Number.isFinite(parsedLimit) && parsedLimit > 0 ? Math.min(parsedLimit, 100) : 20;
    const page = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;
    const offset = (page - 1) * limit;
    
    let articles;
    try {
      articles = await getArticlesByCategory('politics', limit, offset);
    } catch (dbError) {
      console.warn('Database unavailable, using demo data');
      articles = DEMO_POLITICS_ARTICLES;
    }
    
    if (!articles || articles.length === 0) {
      articles = DEMO_POLITICS_ARTICLES.slice(0, limit);
    }
    
    res.json({
      success: true,
      category: 'politics',
      count: articles.length,
      page,
      limit,
      data: articles
    });
  } catch (error) {
    console.error('Error fetching politics news:', error);
    res.json({
      success: true,
      category: 'politics',
      count: DEMO_POLITICS_ARTICLES.length,
      page: 1,
      limit: 20,
      data: DEMO_POLITICS_ARTICLES,
      demo: true
    });
  }
});

module.exports = router;
