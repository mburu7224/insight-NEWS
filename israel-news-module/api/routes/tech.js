/**
 * Tech News API Route
 */

const express = require('express');
const router = express.Router();
const { getArticlesByCategory } = require('../db');

// Demo/Mock data for Tech category
const DEMO_TECH_ARTICLES = [
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
    id: 6,
    title: 'Breakthrough Solar Technology Developed in Israel',
    description: 'Israeli researchers develop breakthrough solar panel technology with 40% efficiency.',
    url: 'https://example.com/israel-solar',
    image_url: 'https://images.unsplash.com/photo-1509391366360-2e959784a276?w=800',
    published_at: new Date(Date.now() - 14400000).toISOString(),
    source: 'Calcalist',
    category_name: 'tech',
    summary: ['40% efficiency breakthrough', 'New solar panel technology', 'Commercial production in 2025'],
    sentiment: 'positive',
    importance: 'high'
  },
  {
    id: 7,
    title: 'Tel Aviv Ranked Among Top Global Tech Hubs',
    description: 'New report places Tel Aviv in top 5 global technology innovation centers.',
    url: 'https://example.com/tel-aviv-tech',
    image_url: 'https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=800',
    published_at: new Date(Date.now() - 28800000).toISOString(),
    source: 'Globes',
    category_name: 'tech',
    summary: ['Tel Aviv in top 5 tech hubs', 'Strong startup ecosystem', 'Government support for innovation'],
    sentiment: 'positive',
    importance: 'medium'
  }
];

// Get tech news
router.get('/', async (req, res) => {
  try {
    const parsedLimit = Number.parseInt(req.query.limit, 10);
    const parsedPage = Number.parseInt(req.query.page, 10);
    const limit = Number.isFinite(parsedLimit) && parsedLimit > 0 ? Math.min(parsedLimit, 100) : 20;
    const page = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;
    const offset = (page - 1) * limit;
    
    let articles;
    try {
      articles = await getArticlesByCategory('tech', limit, offset);
    } catch (dbError) {
      console.warn('Database unavailable, using demo data');
      articles = DEMO_TECH_ARTICLES;
    }
    
    if (!articles || articles.length === 0) {
      articles = DEMO_TECH_ARTICLES.slice(0, limit);
    }
    
    res.json({
      success: true,
      category: 'tech',
      count: articles.length,
      page,
      limit,
      data: articles
    });
  } catch (error) {
    console.error('Error fetching tech news:', error);
    res.json({
      success: true,
      category: 'tech',
      count: DEMO_TECH_ARTICLES.length,
      page: 1,
      limit: 20,
      data: DEMO_TECH_ARTICLES,
      demo: true
    });
  }
});

module.exports = router;
