"""
Israel News Module - Database Connection Utilities
PostgreSQL and Firebase integration
"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Firebase imports
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgreSQLConnection:
    """PostgreSQL database connection manager"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.database = os.getenv('POSTGRES_DB', 'israel_news_db')
        self.user = os.getenv('POSTGRES_USER', 'postgres')
        self.password = os.getenv('POSTGRES_PASSWORD', '')
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info("Connected to PostgreSQL database")
            return self.connection
        except psycopg2.Error as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("PostgreSQL connection closed")
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        if not self.connection:
            self.connect()
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT query and return the inserted ID"""
        if not self.connection:
            self.connect()
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            inserted = None
            try:
                inserted = cursor.fetchone()
            except psycopg2.ProgrammingError:
                inserted = None
            self.connection.commit()
            if inserted and len(inserted) > 0:
                return inserted[0]
            return None
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an UPDATE query and return affected rows"""
        if not self.connection:
            self.connect()
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.rowcount
    
    def insert_article(self, article: Dict) -> int:
        """Insert an article into the database"""
        query = """
            INSERT INTO articles (external_id, title, description, content, url, image_url, 
                               published_at, source, category_id, summary, sentiment, importance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE 
            SET title = EXCLUDED.title, 
                description = EXCLUDED.description,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        params = (
            article.get('external_id'),
            article.get('title'),
            article.get('description'),
            article.get('content'),
            article.get('url'),
            article.get('image_url'),
            article.get('published_at'),
            article.get('source'),
            article.get('category_id'),
            json.dumps(article.get('summary', [])),
            article.get('sentiment'),
            article.get('importance')
        )
        
        result = self.execute_query(query, params)
        return result[0]['id'] if result else None
    
    def get_articles_by_category(self, category: str, limit: int = 20) -> List[Dict]:
        """Get articles by category"""
        query = """
            SELECT a.*, c.name as category_name
            FROM articles a
            JOIN categories c ON a.category_id = c.id
            WHERE c.name = %s
            ORDER BY a.published_at DESC
            LIMIT %s
        """
        return self.execute_query(query, (category, limit))
    
    def get_all_articles(self, limit: int = 50) -> List[Dict]:
        """Get all articles"""
        query = """
            SELECT a.*, c.name as category_name
            FROM articles a
            JOIN categories c ON a.category_id = c.id
            ORDER BY a.published_at DESC
            LIMIT %s
        """
        return self.execute_query(query, (limit,))


class FirebaseConnection:
    """Firebase Firestore database connection manager"""
    
    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path or os.getenv('FIREBASE_CREDENTIALS')
        self.db = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Firebase app"""
        try:
            if not firebase_admin._apps:
                if self.credentials_path and os.path.exists(self.credentials_path):
                    cred = credentials.Certificate(self.credentials_path)
                else:
                    # Try to use default credentials
                    cred = credentials.Certificate(
                        json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT', '{}'))
                    )
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            logger.info("Connected to Firebase Firestore")
        except Exception as e:
            logger.error(f"Error initializing Firebase: {e}")
            raise
    
    def save_article(self, article: Dict):
        """Save an article to Firestore"""
        try:
            doc_ref = self.db.collection('articles').document(article.get('url', ''))
            doc_ref.set({
                'title': article.get('title'),
                'description': article.get('description'),
                'url': article.get('url'),
                'image_url': article.get('image_url'),
                'published_at': article.get('published_at'),
                'source': article.get('source'),
                'category': article.get('category'),
                'summary': article.get('summary', []),
                'sentiment': article.get('sentiment'),
                'importance': article.get('importance'),
                'processed_at': datetime.now().isoformat()
            })
            logger.info(f"Saved article to Firebase: {article.get('title')}")
        except Exception as e:
            logger.error(f"Error saving to Firebase: {e}")
            raise
    
    def get_articles_by_category(self, category: str, limit: int = 20) -> List[Dict]:
        """Get articles by category from Firestore"""
        try:
            docs = self.db.collection('articles')\
                .where('category', '==', category)\
                .order_by('published_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
            
            articles = []
            for doc in docs:
                article = doc.to_dict()
                article['id'] = doc.id
                articles.append(article)
            
            return articles
        except Exception as e:
            logger.error(f"Error fetching from Firebase: {e}")
            return []
    
    def get_all_articles(self, limit: int = 50) -> List[Dict]:
        """Get all articles from Firestore"""
        try:
            docs = self.db.collection('articles')\
                .order_by('published_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
            
            articles = []
            for doc in docs:
                article = doc.to_dict()
                article['id'] = doc.id
                articles.append(article)
            
            return articles
        except Exception as e:
            logger.error(f"Error fetching from Firebase: {e}")
            return []


def main():
    """Test database connections"""
    # Test PostgreSQL
    try:
        pg = PostgreSQLConnection()
        pg.connect()
        articles = pg.get_all_articles(limit=5)
        print(f"PostgreSQL: Found {len(articles)} articles")
        pg.close()
    except Exception as e:
        print(f"PostgreSQL Error: {e}")
    
    # Test Firebase
    try:
        fb = FirebaseConnection()
        articles = fb.get_all_articles(limit=5)
        print(f"Firebase: Found {len(articles)} articles")
    except Exception as e:
        print(f"Firebase Error: {e}")


if __name__ == "__main__":
    main()
