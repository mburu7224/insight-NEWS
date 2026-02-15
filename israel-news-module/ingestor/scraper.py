"""
Israel News Module - Ingestor
Scrapes Israeli news from NewsAPI, RSS feeds, and websites
"""

import os
import json
import time
import logging
import requests
import feedparser
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsScraper:
    """Scrapes news from multiple sources for Israeli news"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the news scraper
        
        Args:
            api_key: NewsAPI.org API key. If not provided, reads from environment variable
        """
        self.api_key = api_key or os.getenv('NEWSAPI_KEY')
        if not self.api_key:
            raise ValueError("NewsAPI.org API key is required. Set NEWSAPI_KEY environment variable.")
        
        # Load feeds configuration
        self.feeds_config = self._load_feeds_config()
        
        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        self.last_request_time = 0
        self.daily_request_count = 0
        self.daily_reset_time = datetime.now()
        
        # Maximum requests per day (free NewsAPI tier: 100/day)
        self.max_daily_requests = 100
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _load_feeds_config(self) -> Dict:
        """Load feeds configuration from feeds.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'feeds.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("feeds.json not found, using default configuration")
            return self._default_feeds_config()
    
    def _default_feeds_config(self) -> Dict:
        """Default feeds configuration"""
        return {
            "sectors": {
                "farming": {
                    "keywords": ["agriculture", "farming", "farmers", "crops", "livestock", "agtech"],
                    "search_queries": ["Israel agriculture farming", "Israeli farmers"]
                },
                "tech": {
                    "keywords": ["technology", "tech", "startup", "innovation", "AI"],
                    "search_queries": ["Israel technology", "Israeli startup", "Tel Aviv tech"]
                },
                "politics": {
                    "keywords": ["politics", "government", "Knesset", "election", "policy"],
                    "search_queries": ["Israel politics", "Israeli government", "Knesset news"]
                },
                "hospitality": {
                    "keywords": ["hotel", "tourism", "restaurant", "hospitality", "travel"],
                    "search_queries": ["Israel tourism", "Israeli hotels", "Israel restaurants"]
                }
            },
            "news_domains": [
                "ynet.co.il", "haaretz.co.il", "timesofisrael.com",
                "calcalist.co.il", "jpost.com", "israelhayom.com"
            ]
        }
    
    def _rate_limit(self):
        """Apply rate limiting between requests"""
        # Check if we need to reset daily counter
        now = datetime.now()
        if (now - self.daily_reset_time).days >= 1:
            self.daily_request_count = 0
            self.daily_reset_time = now
        
        # Check daily limit
        if self.daily_request_count >= self.max_daily_requests:
            wait_time = (datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1) - now).total_seconds()
            logger.warning(f"Daily request limit reached. Waiting {wait_time:.0f} seconds")
            time.sleep(wait_time)
            self.daily_request_count = 0
            self.daily_reset_time = datetime.now()
        
        # Apply request delay
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        self.last_request_time = time.time()
        self.daily_request_count += 1
    
    def fetch_from_newsapi(self, query: str = None, country: str = 'il', 
                           category: str = None, page_size: int = 100) -> List[Dict]:
        """
        Fetch news from NewsAPI.org
        
        Args:
            query: Search query (optional)
            country: Country code (default: il for Israel)
            category: News category (optional)
            page_size: Number of results per page (max 100)
            
        Returns:
            List of news articles
        """
        articles = []
        self._rate_limit()
        
        try:
            # Endpoint for top headlines
            if category:
                url = f"https://newsapi.org/v2/top-headlines"
                params = {
                    'apiKey': self.api_key,
                    'country': country,
                    'category': category,
                    'pageSize': page_size
                }
            elif query:
                url = f"https://newsapi.org/v2/everything"
                params = {
                    'apiKey': self.api_key,
                    'q': query,
                    'domains': ','.join(self.feeds_config.get('news_domains', [])),
                    'language': 'en',
                    'pageSize': page_size,
                    'sortBy': 'publishedAt'
                }
            else:
                url = f"https://newsapi.org/v2/top-headlines"
                params = {
                    'apiKey': self.api_key,
                    'country': country,
                    'pageSize': page_size
                }
            
            logger.info(f"Fetching from NewsAPI: {url}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing NewsAPI response: {e}")
        
        return articles
    
    def fetch_from_rss(self, rss_url: str) -> List[Dict]:
        """
        Fetch news from RSS feed
        
        Args:
            rss_url: URL of the RSS feed
            
        Returns:
            List of news articles
        """
        articles = []
        self._rate_limit()
        
        try:
            logger.info(f"Fetching RSS feed: {rss_url}")
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:50]:  # Limit to 50 entries
                article = {
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', ''),
                    'content': entry.get('content', [{}])[0].get('value', ''),
                    'url': entry.get('link', ''),
                    'image_url': self._extract_rss_image(entry),
                    'published_at': entry.get('published', ''),
                    'source': feed.feed.get('title', ''),
                    'external_id': entry.get('id', entry.get('link', ''))
                }
                articles.append(article)
            
            logger.info(f"Fetched {len(articles)} articles from RSS: {rss_url}")
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {rss_url}: {e}")
        
        return articles
    
    def _extract_rss_image(self, entry: Dict) -> str:
        """Extract image URL from RSS entry"""
        # Try media content
        if 'media_content' in entry:
            for media in entry['media_content']:
                if media.get('type', '').startswith('image'):
                    return media.get('url', '')
        
        # Try media:thumbnail
        if 'media_thumbnail' in entry:
            return entry['media_thumbnail'][0].get('url', '')
        
        # Try enclosures
        if 'enclosures' in entry:
            for enclosure in entry['enclosures']:
                if enclosure.get('type', '').startswith('image'):
                    return enclosure.get('url', '')
        
        return ''
    
    def fetch_from_website(self, url: str) -> List[Dict]:
        """
        Fetch and parse news from website
        
        Args:
            url: URL of the news website
            
        Returns:
            List of news articles
        """
        articles = []
        self._rate_limit()
        
        try:
            logger.info(f"Fetching website: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Try to find article elements (generic approach)
            article_elements = soup.find_all('article')[:20]
            
            for article_elem in article_elements:
                try:
                    title_elem = article_elem.find(['h1', 'h2', 'h3', 'a'])
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    link = ''
                    if title_elem and title_elem.name == 'a':
                        link = title_elem.get('href', '')
                    else:
                        link_elem = article_elem.find('a', href=True)
                        link = link_elem.get('href', '') if link_elem else ''
                    
                    # Make absolute URL
                    if link and not link.startswith('http'):
                        from urllib.parse import urljoin
                        link = urljoin(url, link)
                    
                    if title and link:
                        articles.append({
                            'title': title,
                            'description': '',
                            'content': '',
                            'url': link,
                            'image_url': '',
                            'published_at': '',
                            'source': soup.title.string if soup.title else url
                        })
                        
                except Exception as e:
                    logger.debug(f"Error parsing article element: {e}")
                    continue
            
            logger.info(f"Fetched {len(articles)} articles from website: {url}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching website {url}: {e}")
        
        return articles
    
    def fetch_all_sectors(self, use_rss: bool = True) -> Dict[str, List[Dict]]:
        """
        Fetch news for all configured sectors
        
        Args:
            use_rss: Whether to also fetch from RSS feeds
            
        Returns:
            Dictionary mapping sector names to article lists
        """
        all_articles = {
            'farming': [],
            'tech': [],
            'politics': [],
            'hospitality': [],
            'general': []
        }
        
        sectors = self.feeds_config.get('sectors', {})
        
        # Fetch by sector search queries
        for sector, config in sectors.items():
            queries = config.get('search_queries', [])
            
            for query in queries[:2]:  # Limit queries per sector
                articles = self.fetch_from_newsapi(query=query)
                
                for article in articles:
                    article['sector'] = sector
                    all_articles[sector].append(article)
        
        # Fetch general Israeli news
        general_articles = self.fetch_from_newsapi(country='il')
        for article in general_articles:
            article['sector'] = 'general'
            all_articles['general'].append(article)
        
        # Optionally fetch from RSS feeds
        if use_rss:
            rss_feeds = self._get_rss_feeds()
            for sector, feeds in rss_feeds.items():
                for feed_url in feeds:
                    rss_articles = self.fetch_from_rss(feed_url)
                    for article in rss_articles:
                        article['sector'] = sector
                        all_articles[sector].append(article)
        
        # Deduplicate by URL
        for sector in all_articles:
            seen_urls = set()
            unique_articles = []
            for article in all_articles[sector]:
                url = article.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_articles.append(article)
            all_articles[sector] = unique_articles
        
        return all_articles
    
    def _get_rss_feeds(self) -> Dict[str, List[str]]:
        """Get RSS feed URLs for Israeli news sources"""
        return {
            'general': [
                'https://www.timesofisrael.com/feed/',
                'https://www.jpost.com/Rss/RssFeeds.aspx'
            ],
            'tech': [
                'https://www.calcalist.co.il/General/RssFeed.xml'
            ],
            'farming': [
                'https://www.israel21c.org/feed/'
            ]
        }
    
    def fetch_by_category(self, category: str) -> List[Dict]:
        """
        Fetch news for a specific category
        
        Args:
            category: Category name (farming, tech, politics, hospitality, general)
            
        Returns:
            List of news articles
        """
        sector_config = self.feeds_config.get('sectors', {}).get(category, {})
        queries = sector_config.get('search_queries', [f"Israel {category}"])
        
        articles = []
        for query in queries[:3]:
            fetched = self.fetch_from_newsapi(query=query)
            for article in fetched:
                article['sector'] = category
                articles.append(article)
        
        # Deduplicate
        seen_urls = set()
        unique_articles = []
        for article in articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles
    
    def to_json_format(self, articles: List[Dict]) -> List[Dict]:
        """
        Convert articles to standardized JSON format
        
        Args:
            articles: List of raw articles
            
        Returns:
            List of formatted articles
        """
        formatted = []
        
        for article in articles:
            formatted_article = {
                'external_id': article.get('external_id', article.get('url', '')),
                'title': article.get('title', ''),
                'description': article.get('description', '') or article.get('summary', ''),
                'content': article.get('content', ''),
                'url': article.get('url', ''),
                'image_url': article.get('image_url', '') or article.get('urlToImage', ''),
                'published_at': article.get('published_at', '') or article.get('publishedAt', ''),
                'source': article.get('source', {}).get('name', '') if isinstance(article.get('source'), dict) else article.get('source', ''),
                'category': article.get('sector', article.get('category', 'general'))
            }
            formatted.append(formatted_article)
        
        return formatted


def main():
    """Main function to test the scraper"""
    try:
        scraper = NewsScraper()
        
        # Fetch all sectors
        print("Fetching news for all sectors...")
        all_news = scraper.fetch_all_sectors(use_rss=False)
        
        for sector, articles in all_news.items():
            print(f"\n{sector.upper()}: {len(articles)} articles")
            for article in articles[:3]:
                print(f"  - {article.get('title', 'No title')[:60]}...")
        
        # Save to JSON
        output_path = os.path.join(os.path.dirname(__file__), 'output.json')
        with open(output_path, 'w') as f:
            json.dump(all_news, f, indent=2)
        print(f"\nSaved to {output_path}")
        
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set NEWSAPI_KEY environment variable")


if __name__ == "__main__":
    main()
