"""
Israel News Module - Asset Automator
Handles image fetching, hosting, and URL management
Supports AWS S3, Cloudinary, and local file storage
"""

import os
import json
import logging
import hashlib
import requests
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageUploader:
    """Handles image uploading to cloud storage with caching and fallback"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize the image uploader
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Storage provider configuration
        self.provider = os.getenv('IMAGE_STORAGE_PROVIDER', 'local')  # s3, cloudinary, local
        
        # AWS S3 configuration
        self.s3_bucket = os.getenv('AWS_S3_BUCKET', '')
        self.s3_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Cloudinary configuration
        self.cloudinary_cloud = os.getenv('CLOUDINARY_CLOUD_NAME', '')
        self.cloudinary_api_key = os.getenv('CLOUDINARY_API_KEY', '')
        self.cloudinary_api_secret = os.getenv('CLOUDINARY_API_SECRET', '')
        
        # Local storage configuration
        self.local_storage_path = os.getenv('LOCAL_STORAGE_PATH', './uploads')
        
        # Initialize storage clients
        self._init_storage()
        
        # Cache for already uploaded images
        self.url_cache: Dict[str, str] = {}
    
    def _init_storage(self):
        """Initialize storage provider"""
        if self.provider == 's3':
            try:
                import boto3
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.s3_region,
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                )
                logger.info("AWS S3 client initialized")
            except ImportError:
                logger.warning("boto3 not installed, falling back to local storage")
                self.provider = 'local'
            except Exception as e:
                logger.error(f"Error initializing S3: {e}")
                self.provider = 'local'
        
        elif self.provider == 'cloudinary':
            try:
                import cloudinary
                import cloudinary.uploader
                cloudinary.config(
                    cloud_name=self.cloudinary_cloud,
                    api_key=self.cloudinary_api_key,
                    api_secret=self.cloudinary_api_secret
                )
                self.cloudinary = cloudinary
                logger.info("Cloudinary initialized")
            except ImportError:
                logger.warning("cloudinary not installed, falling back to local storage")
                self.provider = 'local'
        
        # Ensure local storage directory exists
        if self.provider == 'local':
            os.makedirs(self.local_storage_path, exist_ok=True)
            logger.info(f"Local storage initialized at: {self.local_storage_path}")
    
    def _get_image_hash(self, url: str) -> str:
        """Generate unique hash for image URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None
    
    def upload_image(self, url: str, article_id: str = None) -> str:
        """
        Upload image from URL to storage
        
        Args:
            url: Original image URL
            article_id: Optional article ID for naming
            
        Returns:
            Hosted image URL or fallback URL
        """
        if not url:
            return self._get_fallback_image()
        
        # Check cache
        if url in self.url_cache:
            return self.url_cache[url]
        
        # Download image
        image_data = self._download_image(url)
        if not image_data:
            return self._get_fallback_image()
        
        # Optimize image before upload
        image_data = self._optimize_image(image_data)
        
        # Determine file extension
        ext = self._get_extension(url, image_data)
        
        # Generate filename
        filename = f"{article_id or self._get_image_hash(url)}{ext}"
        
        # Upload based on provider
        try:
            if self.provider == 's3':
                hosted_url = self._upload_to_s3(image_data, filename)
            elif self.provider == 'cloudinary':
                hosted_url = self._upload_to_cloudinary(image_data, filename)
            else:
                hosted_url = self._upload_locally(image_data, filename)
            
            # Cache the result
            self.url_cache[url] = hosted_url
            return hosted_url
            
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            return self._get_fallback_image()
    
    def _upload_to_s3(self, image_data: bytes, filename: str) -> str:
        """Upload to AWS S3"""
        import boto3
        
        s3_client = boto3.client(
            's3',
            region_name=self.s3_region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        key = f"news-images/{datetime.now().year}/{datetime.now().month:02d}/{filename}"
        
        s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=key,
            Body=image_data,
            ContentType='image/jpeg',
            ACL='public-read'
        )
        
        url = f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com/{key}"
        logger.info(f"Uploaded to S3: {url}")
        return url
    
    def _upload_to_cloudinary(self, image_data: bytes, filename: str) -> str:
        """Upload to Cloudinary"""
        import cloudinary.uploader
        import io
        
        # Upload from memory
        result = cloudinary.uploader.upload(
            io.BytesIO(image_data),
            public_id=f"news/{filename.split('.')[0]}",
            folder="israel-news"
        )
        
        url = result.get('secure_url', '')
        logger.info(f"Uploaded to Cloudinary: {url}")
        return url
    
    def _upload_locally(self, image_data: bytes, filename: str) -> str:
        """Upload to local storage"""
        # Create date-based subdirectory
        date_path = f"{datetime.now().year}/{datetime.now().month:02d}"
        full_path = os.path.join(self.local_storage_path, date_path)
        os.makedirs(full_path, exist_ok=True)
        
        file_path = os.path.join(full_path, filename)
        
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # Return relative URL (actual serving would need a web server)
        url = f"/uploads/{date_path}/{filename}"
        logger.info(f"Uploaded locally: {url}")
        return url
    
    def _get_extension(self, url: str, image_data: bytes) -> str:
        """Determine file extension"""
        # Try from URL
        if url:
            url_lower = url.lower()
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                if ext in url_lower:
                    return ext
        
        # Try from content type
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_data))
            return f".{img.format.lower()}"
        except:
            pass
        
        return '.jpg'  # Default
    
    def _optimize_image(self, image_data: bytes, max_width: int = 800, quality: int = 85) -> bytes:
        """
        Optimize image by resizing and compressing
        
        Args:
            image_data: Original image data
            max_width: Maximum width in pixels
            quality: JPEG quality (1-100)
            
        Returns:
            Optimized image data
        """
        try:
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'P' else None)
                img = rgb_img
            
            # Resize if wider than max_width
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Compress to JPEG
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            
            logger.info(f"Optimized image: {len(image_data)} -> {len(output.getvalue())} bytes ({len(output.getvalue())/len(image_data)*100:.1f}%)")
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error optimizing image: {e}")
            return image_data  # Return original if optimization fails
    
    def _get_fallback_image(self) -> str:
        """Get fallback image URL for articles without images"""
        return os.getenv('FALLBACK_IMAGE_URL', 'https://via.placeholder.com/800x450?text=No+Image')
    
    def process_article_images(self, articles: List[Dict]) -> List[Dict]:
        """
        Process images for a list of articles
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Articles with updated image URLs
        """
        for article in articles:
            original_url = article.get('image_url', '')
            article_id = article.get('id') or article.get('external_id', '')
            
            if original_url:
                article['image_url'] = self.upload_image(original_url, article_id)
            else:
                article['image_url'] = self._get_fallback_image()
        
        return articles
    
    def batch_upload(self, urls: List[str]) -> List[str]:
        """
        Upload multiple images
        
        Args:
            urls: List of image URLs
            
        Returns:
            List of hosted image URLs
        """
        results = []
        for url in urls:
            results.append(self.upload_image(url))
        return results


class ImageGenerator:
    """Generates placeholder images for articles without images"""
    
    def __init__(self):
        self.fallback_templates = {
            'farming': 'https://via.placeholder.com/800x450/e8f5e9/1b5e20?text=🇮🇱+Agriculture',
            'tech': 'https://via.placeholder.com/800x450/e3f2fd/0d47a1?text=💻+Technology',
            'politics': 'https://via.placeholder.com/800x450/f3e5f5/4a148c?text=🏛️+Politics',
            'hospitality': 'https://via.placeholder.com/800x450/fff3e0/e65100?text=🏨+Hospitality',
            'general': 'https://via.placeholder.com/800x450/ffffff/333333?text=📰+Israel+News'
        }
    
    def get_category_image(self, category: str) -> str:
        """Get a placeholder image for a category"""
        return self.fallback_templates.get(category.lower(), 
            self.fallback_templates['general'])
    
    def generate_placeholder(self, title: str, category: str = 'general') -> str:
        """
        Generate a placeholder image URL based on title and category
        
        Args:
            title: Article title
            category: Article category
            
        Returns:
            Placeholder image URL
        """
        # Encode title for URL
        import urllib.parse
        encoded_title = urllib.parse.quote(title[:30] + '...')
        
        # Use dynamic placeholder service
        category_emoji = {
            'farming': '🌾',
            'tech': '💻',
            'politics': '🏛️',
            'hospitality': '🏨',
            'general': '📰'
        }
        
        emoji = category_emoji.get(category.lower(), '📰')
        
        # Return category-specific placeholder
        return self.get_category_image(category)


def main():
    """Test the image uploader"""
    # Test with sample URLs
    uploader = ImageUploader()
    
    test_urls = [
        'https://example.com/image1.jpg',
        'https://example.com/image2.png'
    ]
    
    print("Testing image uploader...")
    print(f"Provider: {uploader.provider}")
    
    # Test placeholder generator
    generator = ImageGenerator()
    for category in ['farming', 'tech', 'politics', 'hospitality', 'general']:
        print(f"\n{category}: {generator.get_category_image(category)}")


if __name__ == "__main__":
    main()
