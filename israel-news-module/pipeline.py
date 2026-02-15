"""
Israel News Module - Processing Pipeline
Orchestrates the complete news processing flow:
Ingestor → Processor → Asset Automator → Database
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsPipeline:
    """Orchestrates the complete news processing pipeline"""
    
    def __init__(self, config: dict = None):
        """
        Initialize the pipeline
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.ingestor = None
        self.processor = None
        self.uploader = None
        self.db = None
        
        # Load environment
        load_dotenv()
        
        # Initialize components
        self._init_components()
    
    def _init_components(self):
        """Initialize pipeline components"""
        # Import components
        try:
            from ingestor.scraper import NewsScraper
            self.ingestor = NewsScraper()
            logger.info("✓ Ingestor initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Ingestor: {e}")
        
        try:
            from processor.summarizer import NewsProcessor
            self.processor = NewsProcessor()
            logger.info("✓ Processor initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Processor: {e}")
        
        try:
            from asset_automator.uploader import ImageUploader
            self.uploader = ImageUploader()
            logger.info("✓ Asset Automator initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Asset Automator: {e}")
        
        try:
            from data.database import PostgreSQLConnection
            self.db = PostgreSQLConnection()
            logger.info("✓ Database initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Database: {e}")
    
    def run_ingestor(self, categories: list = None) -> dict:
        """
        Run the ingestor to fetch raw news
        
        Args:
            categories: List of categories to fetch (default: all)
        
        Returns:
            Dictionary of articles by category
        """
        if not self.ingestor:
            logger.error("Ingestor not initialized")
            return {}
        
        categories = categories or ['farming', 'tech', 'politics', 'hospitality', 'general']
        all_articles = {}
        
        for category in categories:
            logger.info(f"Fetching {category} news...")
            try:
                articles = self.ingestor.fetch_by_category(category)
                all_articles[category] = articles
                logger.info(f"  → Found {len(articles)} articles")
            except Exception as e:
                logger.error(f"  → Error fetching {category}: {e}")
                all_articles[category] = []
        
        return all_articles
    
    def run_processor(self, articles: list) -> list:
        """
        Run the processor to summarize and categorize articles
        
        Args:
            articles: List of raw articles
        
        Returns:
            List of processed articles
        """
        if not self.processor:
            logger.warning("Processor not initialized, returning raw articles")
            return articles
        
        logger.info(f"Processing {len(articles)} articles...")
        processed = self.processor.process_batch(articles)
        logger.info(f"  → Processed {len(processed)} articles")
        
        return processed
    
    def run_asset_automator(self, articles: list) -> list:
        """
        Run the asset automator to handle images
        
        Args:
            articles: List of articles
        
        Returns:
            List of articles with processed image URLs
        """
        if not self.uploader:
            logger.warning("Asset Automator not initialized, keeping original images")
            return articles
        
        logger.info(f"Processing images for {len(articles)} articles...")
        processed = self.uploader.process_article_images(articles)
        logger.info(f"  → Processed images for {len(processed)} articles")
        
        return processed
    
    def save_to_database(self, articles: list) -> int:
        """
        Save articles to database
        
        Args:
            articles: List of processed articles
        
        Returns:
            Number of articles saved
        """
        if not self.db:
            logger.warning("Database not initialized, skipping save")
            return 0
        
        saved = 0
        for article in articles:
            try:
                # Get category ID
                category = article.get('category', 'general')
                categories = self.db.execute_query(
                    "SELECT id FROM categories WHERE name = %s",
                    (category,)
                )
                
                if categories:
                    article['category_id'] = categories[0]['id']
                    self.db.insert_article(article)
                    saved += 1
            except Exception as e:
                logger.error(f"Error saving article: {e}")
        
        logger.info(f"  → Saved {saved} articles to database")
        return saved
    
    def run_full_pipeline(self, categories: list = None, save: bool = True) -> dict:
        """
        Run the complete pipeline
        
        Args:
            categories: Categories to process
            save: Whether to save to database
        
        Returns:
            Pipeline results
        """
        start_time = datetime.now()
        results = {
            'start_time': start_time.isoformat(),
            'categories': {},
            'total_articles': 0,
            'processed_articles': 0,
            'saved_articles': 0,
            'errors': []
        }
        
        categories = categories or ['farming', 'tech', 'politics', 'hospitality', 'general']
        
        logger.info("=" * 50)
        logger.info("Starting Israel News Pipeline")
        logger.info("=" * 50)
        
        # Step 1: Ingest
        logger.info("\n[1/4] Running Ingestor...")
        raw_articles = self.run_ingestor(categories)
        
        for category, articles in raw_articles.items():
            results['categories'][category] = {
                'raw_count': len(articles)
            }
            results['total_articles'] += len(articles)
        
        # Step 2: Process (summarize & categorize)
        logger.info("\n[2/4] Running Processor...")
        all_processed = []
        
        for category, articles in raw_articles.items():
            if articles:
                processed = self.run_processor(articles)
                all_processed.extend(processed)
                results['categories'][category]['processed_count'] = len(processed)
        
        results['processed_articles'] = len(all_processed)
        
        # Step 3: Asset Automator (images)
        logger.info("\n[3/4] Running Asset Automator...")
        final_articles = self.run_asset_automator(all_processed)
        
        # Step 4: Save to database
        if save:
            logger.info("\n[4/4] Saving to Database...")
            results['saved_articles'] = self.save_to_database(final_articles)
        
        # Complete
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        results['end_time'] = end_time.isoformat()
        results['duration_seconds'] = duration
        
        logger.info("\n" + "=" * 50)
        logger.info("Pipeline Complete!")
        logger.info(f"  Total raw articles: {results['total_articles']}")
        logger.info(f"  Processed articles: {results['processed_articles']}")
        logger.info(f"  Saved to database: {results['saved_articles']}")
        logger.info(f"  Duration: {duration:.2f}s")
        logger.info("=" * 50)
        
        return results
    
    def run_single_category(self, category: str, save: bool = True) -> dict:
        """
        Run pipeline for a single category
        
        Args:
            category: Category name
            save: Whether to save to database
        
        Returns:
            Category results
        """
        return self.run_full_pipeline(categories=[category], save=save)
    
    def close(self):
        """Clean up resources"""
        if self.db:
            self.db.close()
            logger.info("Database connection closed")


def main():
    """Main entry point for the pipeline"""
    parser = argparse.ArgumentParser(description='Israel News Processing Pipeline')
    parser.add_argument(
        '--category', 
        '-c',
        choices=['farming', 'tech', 'politics', 'hospitality', 'general', 'all'],
        default='all',
        help='Category to process'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Skip saving to database'
    )
    parser.add_argument(
        '--verbose', 
        '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine categories
    if args.category == 'all':
        categories = ['farming', 'tech', 'politics', 'hospitality', 'general']
    else:
        categories = [args.category]
    
    # Run pipeline
    pipeline = NewsPipeline()
    
    try:
        results = pipeline.run_full_pipeline(
            categories=categories,
            save=not args.no_save
        )
        
        # Print summary
        print("\n" + "=" * 40)
        print("PIPELINE SUMMARY")
        print("=" * 40)
        
        for cat, data in results['categories'].items():
            print(f"{cat:15} | Raw: {data.get('raw_count', 0):3} | Processed: {data.get('processed_count', 0):3}")
        
        print("-" * 40)
        print(f"{'TOTAL':15} | Raw: {results['total_articles']:3} | Processed: {results['processed_articles']:3}")
        print(f"Saved: {results['saved_articles']}")
        print(f"Duration: {results['duration_seconds']:.2f}s")
        
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
    except Exception as e:
        print(f"\nPipeline error: {e}")
        raise
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
