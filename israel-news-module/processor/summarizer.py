"""
Israel News Module - Processor
Uses OpenAI to summarize and categorize Israeli news
"""

import os
import json
import logging
import hashlib
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsProcessor:
    """Processes news articles using OpenAI for summarization and categorization"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the NewsProcessor
        
        Args:
            api_key: OpenAI API key. If not provided, reads from environment variable
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Sector keywords for categorization
        self.sector_keywords = {
            'farming': ['agriculture', 'farming', 'farmers', 'crops', 'livestock', 'agtech', 'agricultural'],
            'tech': ['technology', 'tech', 'startup', 'innovation', 'AI', 'cybersecurity', 'software', 'digital'],
            'politics': ['politics', 'government', 'Knesset', 'election', 'policy', 'minister', 'parliament'],
            'hospitality': ['hotel', 'tourism', 'restaurant', 'hospitality', 'travel', 'accommodation']
        }
    
    def categorize_article(self, title: str, description: str = None) -> str:
        """
        Categorize an article into one of the sectors
        
        Args:
            title: Article title
            description: Article description
            
        Returns:
            Sector category (farming, tech, politics, hospitality, or general)
        """
        text = f"{title} {description or ''}".lower()
        
        for sector, keywords in self.sector_keywords.items():
            if any(keyword in text for keyword in keywords):
                return sector
        
        return 'general'
    
    def summarize_article(self, title: str, description: str = None, content: str = None) -> Dict:
        """
        Generate a 3-bullet summary for an article using OpenAI
        
        Args:
            title: Article title
            description: Article description
            content: Full article content
            
        Returns:
            Dictionary with summary bullets and metadata
        """
        # Combine available text
        text = f"Title: {title}\n"
        if description:
            text += f"Description: {description}\n"
        if content:
            text += f"Content: {content[:1000]}"  # Limit content length
        
        prompt = f"""You are a news analyst specializing in Israeli news. 
Analyze the following article and provide exactly 3 bullet points summarizing the key information.
Each bullet point should be concise (max 20 words) and capture the essential information.

Article:
{text}

Provide your response in the following JSON format:
{{
    "bullets": [
        "bullet 1",
        "bullet 2", 
        "bullet 3"
    ],
    "sentiment": "positive/negative/neutral",
    "importance": "high/medium/low"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a news analysis assistant that summarizes Israeli news into concise bullet points."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON response
            try:
                summary = json.loads(result)
                return {
                    'bullets': summary.get('bullets', []),
                    'sentiment': summary.get('sentiment', 'neutral'),
                    'importance': summary.get('importance', 'medium'),
                    'success': True
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text
                return {
                    'bullets': [result],
                    'sentiment': 'neutral',
                    'importance': 'medium',
                    'success': True,
                    'raw_response': result
                }
                
        except Exception as e:
            logger.error(f"Error summarizing article: {e}")
            return {
                'bullets': [],
                'sentiment': 'neutral',
                'importance': 'medium',
                'success': False,
                'error': str(e)
            }
    
    def process_article(self, article: Dict) -> Dict:
        """
        Process a single article - categorize and summarize
        
        Args:
            article: Raw article from NewsAPI
            
        Returns:
            Processed article with category and summary
        """
        title = article.get('title', '')
        description = article.get('description', '')
        content = article.get('content', '')
        
        # Categorize
        category = self.categorize_article(title, description)
        
        # Summarize
        summary = self.summarize_article(title, description, content)
        
        return {
            'id': hashlib.sha256(article.get('url', '').encode('utf-8')).hexdigest() if article.get('url') else None,
            'title': title,
            'description': description,
            'url': article.get('url', ''),
            'image_url': article.get('urlToImage', ''),
            'published_at': article.get('publishedAt', ''),
            'source': article.get('source', {}).get('name', ''),
            'category': category,
            'summary': summary.get('bullets', []),
            'sentiment': summary.get('sentiment', 'neutral'),
            'importance': summary.get('importance', 'medium'),
            'processed_at': datetime.now().isoformat()
        }
    
    def process_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Process a batch of articles
        
        Args:
            articles: List of raw articles
            
        Returns:
            List of processed articles
        """
        processed = []
        
        for article in articles:
            try:
                processed_article = self.process_article(article)
                processed.append(processed_article)
            except Exception as e:
                logger.error(f"Error processing article: {e}")
                continue
        
        logger.info(f"Processed {len(processed)} articles")
        return processed
    
    def filter_by_sector(self, articles: List[Dict], sector: str) -> List[Dict]:
        """
        Filter articles by sector
        
        Args:
            articles: List of processed articles
            sector: Sector to filter by
            
        Returns:
            Filtered list of articles
        """
        return [a for a in articles if a.get('category') == sector.lower()]


def main():
    """Main function to test the processor"""
    try:
        processor = NewsProcessor()
        
        # Test article
        test_article = {
            'title': 'Israeli Tech Startup Raises $50M in Series B Funding',
            'description': 'A Tel Aviv-based technology company has secured major investment',
            'url': 'https://example.com/article',
            'urlToImage': 'https://example.com/image.jpg',
            'publishedAt': datetime.now().isoformat(),
            'source': {'name': 'TechCrunch'},
            'content': 'Full article content here...'
        }
        
        # Process article
        result = processor.process_article(test_article)
        print(json.dumps(result, indent=2))
        
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable")


if __name__ == "__main__":
    main()
