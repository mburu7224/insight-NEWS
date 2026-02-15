/**
 * Israel News Module - Database Connection (Node.js)
 * PostgreSQL and Firebase integration
 */

require('dotenv').config();
const { Pool } = require('pg');
const admin = require('firebase-admin');

// PostgreSQL connection pool
const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: process.env.POSTGRES_PORT || 5432,
  database: process.env.POSTGRES_DB || 'israel_news_db',
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || ''
});

// Firebase initialization
let firebaseInitialized = false;
try {
  if (process.env.FIREBASE_SERVICE_ACCOUNT) {
    const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount)
    });
    firebaseInitialized = true;
  }
} catch (error) {
  console.warn('Firebase initialization failed:', error.message);
}

// Get articles by category from PostgreSQL
async function getArticlesByCategory(category, limit = 20, offset = 0) {
  try {
    const result = await pool.query(
      `SELECT a.*, c.name as category_name 
       FROM articles a 
       JOIN categories c ON a.category_id = c.id 
       WHERE c.name = $1 
       ORDER BY a.published_at DESC 
       LIMIT $2
       OFFSET $3`,
      [category, limit, offset]
    );
    return result.rows;
  } catch (error) {
    console.error('Error fetching articles by category:', error);
    // Try Firebase as fallback
    if (firebaseInitialized) {
      return getArticlesFromFirebase(category, limit);
    }
    return [];
  }
}

// Get all articles from PostgreSQL
async function getAllArticles(limit = 50, offset = 0) {
  try {
    const result = await pool.query(
      `SELECT a.*, c.name as category_name 
       FROM articles a 
       JOIN categories c ON a.category_id = c.id 
       ORDER BY a.published_at DESC 
       LIMIT $1
       OFFSET $2`,
      [limit, offset]
    );
    return result.rows;
  } catch (error) {
    console.error('Error fetching all articles:', error);
    // Try Firebase as fallback
    if (firebaseInitialized) {
      return getAllArticlesFromFirebase(limit);
    }
    return [];
  }
}

// Get articles from Firebase (fallback)
async function getArticlesFromFirebase(category, limit = 20) {
  try {
    const db = admin.firestore();
    const snapshot = await db.collection('articles')
      .where('category', '==', category)
      .orderBy('published_at', 'desc')
      .limit(limit)
      .get();
    
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
  } catch (error) {
    console.error('Error fetching from Firebase:', error);
    return [];
  }
}

// Get all articles from Firebase (fallback)
async function getAllArticlesFromFirebase(limit = 50) {
  try {
    const db = admin.firestore();
    const snapshot = await db.collection('articles')
      .orderBy('published_at', 'desc')
      .limit(limit)
      .get();
    
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
  } catch (error) {
    console.error('Error fetching from Firebase:', error);
    return [];
  }
}

// Save article to PostgreSQL
async function saveArticle(article) {
  try {
    // First get category ID
    const categoryResult = await pool.query(
      'SELECT id FROM categories WHERE name = $1',
      [article.category]
    );
    
    if (categoryResult.rows.length === 0) {
      console.error('Category not found:', article.category);
      return null;
    }
    
    const categoryId = categoryResult.rows[0].id;
    
    const result = await pool.query(
      `INSERT INTO articles (external_id, title, description, content, url, image_url, 
                          published_at, source, category_id, summary, sentiment, importance)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
       ON CONFLICT (url) DO UPDATE 
       SET title = EXCLUDED.title, 
           description = EXCLUDED.description,
           updated_at = CURRENT_TIMESTAMP
       RETURNING id`,
      [
        article.external_id,
        article.title,
        article.description,
        article.content,
        article.url,
        article.image_url,
        article.published_at,
        article.source,
        categoryId,
        JSON.stringify(article.summary),
        article.sentiment,
        article.importance
      ]
    );
    
    return result.rows[0].id;
  } catch (error) {
    console.error('Error saving article:', error);
    return null;
  }
}

// Save article to Firebase
async function saveArticleToFirebase(article) {
  try {
    const db = admin.firestore();
    await db.collection('articles').doc(article.url).set(article);
    return true;
  } catch (error) {
    console.error('Error saving to Firebase:', error);
    return false;
  }
}

module.exports = {
  pool,
  getArticlesByCategory,
  getAllArticles,
  saveArticle,
  saveArticleToFirebase
};
