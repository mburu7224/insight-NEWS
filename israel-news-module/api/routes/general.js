/**
 * General News API Route
 */

const express = require('express');
const router = express.Router();
const { getAllArticles } = require('../db');

// Demo/Mock data for when database is unavailable
const DEMO_ARTICLES = [
  {
    id: 1,
    title: 'Israeli Tech Startups Raise Record $15B in 2024',
    description: 'Israel technology sector sees unprecedented growth with AI and cybersecurity leading the way.',
    url: 'https://example.com/israel-tech-startups',
    image_url: 'https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=800',
    published_at: new Date().toISOString(),
    source: 'TechCrunch',
    category_name: 'tech',
    summary: ['Record $15B funding in 2024', 'AI startups dominate investment', 'Cybersecurity sector growing 40%'],
    sentiment: 'positive',
    importance: 'high'
  },
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
    id: 5,
    description: 'Israeli researchers develop breakthrough solar panel technology with 40% efficiency.',
    image_url: 'https://images.unsplash.com/photo-1509391366360-2e959784a276?w=800',
    published_at: new Date(Date.now() - 14400000).toISOString(),
    category_name: 'tech',
    sentiment: 'positive',
    source: 'Calcalist',
    summary: ['40% efficiency breakthrough', 'New solar panel technology', 'Commercial production in 2025'],
    title: 'Breakthrough Solar Technology Developed in Israel',
    url: 'https://example.com/israel-solar'
  }
];

// Get all general news
router.get('/', async (req, res) => {
  try {
    const parsedLimit = Number.parseInt(req.query.limit, 10);
    const parsedPage = Number.parseInt(req.query.page, 10);
    const limit = Number.isFinite(parsedLimit) && parsedLimit > 0 ? Math.min(parsedLimit, 100) : 20;
    const page = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;
    const offset = (page - 1) * limit;
    
    let articles;
    try {
      articles = await getAllArticles(limit, offset);
    } catch (dbError) {
      // Database unavailable - use demo data
      console.warn('Database unavailable, using demo data:', dbError.message);
      articles = DEMO_ARTICLES;
    }
    
    // If no articles from database, use demo data
    if (!articles || articles.length === 0) {
      articles = DEMO_ARTICLES.slice(0, limit);
    }
    
    res.json({
      success: true,
      category: 'general',
      count: articles.length,
      page,
      limit,
      data: articles
    });
  } catch (error) {
    console.error('Error fetching general news:', error);
    // Return demo data on error
    res.json({
      success: true,
      category: 'general',
      count: DEMO_ARTICLES.length,
      page: 1,
      limit: 20,
      data: DEMO_ARTICLES,
      demo: true
    });
  }
});

module.exports = router;
