#!/usr/bin/env python3
"""
Meme Material Radar - Reddit Post Monitoring Tool

This script monitors Reddit subreddits for fast-rising posts and logs them
when they exceed configured upvote rate thresholds.

Author: Meme Material Radar
Version: 1.0
"""

import os
import sys
import time
import logging
import threading
import requests
import hashlib
import json
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
from pathlib import Path

import praw
from dotenv import load_dotenv
from PIL import Image
import openai

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import SUBREDDITS, POST_TRACKING, LOGGING, REDDIT_API, IMAGE_PROCESSING, SUMMARIZATION, MEME_PACKAGES


@dataclass
class PostSnapshot:
    """Snapshot of post data at a specific time."""
    timestamp: datetime
    score: int
    num_comments: int

@dataclass
class PostData:
    """Data structure to track post information with dynamic threshold support."""
    id: str
    title: str
    url: str
    score: int
    upvote_rate: float
    comment_rate: float
    created_utc: float
    subreddit: str
    last_checked: datetime
    comment_count: int = 0
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    summary: Optional[str] = None
    # New fields for dynamic threshold system
    snapshots: Optional[List[PostSnapshot]] = None
    is_tracking: bool = False  # Whether we're actively tracking this post
    has_triggered: bool = False  # Whether this post has already triggered action
    initial_rate: float = 0.0  # Rate calculated from first snapshot


class RedditMonitor:
    """Main class for monitoring Reddit posts."""
    
    def __init__(self):
        """Initialize the Reddit monitor with API credentials and logging."""
        self.setup_logging()
        self.setup_reddit_api()
        self.tracked_posts: Dict[str, PostData] = {}
        self.running = False
        
    def setup_logging(self):
        """Configure logging for the application."""
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(LOGGING['log_file']), exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, LOGGING['log_level']),
            format=LOGGING['log_format'],
            datefmt=LOGGING['date_format'],
            handlers=[
                logging.FileHandler(LOGGING['log_file']),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_reddit_api(self):
        """Initialize Reddit API connection using environment variables."""
        # Load environment variables from config/.env
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
        load_dotenv(env_path)
        
        # Get Reddit API credentials
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        username = os.getenv('REDDIT_USERNAME')
        password = os.getenv('REDDIT_PASSWORD')
        user_agent = os.getenv('REDDIT_USER_AGENT')
        
        # Validate credentials
        if not all([client_id, client_secret, username, password, user_agent]):
            self.logger.error("Missing Reddit API credentials. Please check your .env file.")
            sys.exit(1)
            
        # Initialize Reddit API
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                username=username,
                password=password,
                user_agent=user_agent
            )
            # Test the connection
            self.reddit.user.me()
            self.logger.info("Successfully connected to Reddit API")
        except Exception as e:
            self.logger.error(f"Failed to connect to Reddit API: {e}")
            sys.exit(1)
            
        # Setup OpenAI API if summarization is enabled
        if SUMMARIZATION['enabled']:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                self.logger.info("OpenAI API configured for summarization")
            else:
                self.logger.warning("OpenAI API key not found. Summarization will be disabled.")
                SUMMARIZATION['enabled'] = False
            
    def get_post_key(self, subreddit: str, post_id: str) -> str:
        """Generate a unique key for a post."""
        return f"{subreddit}:{post_id}"
        
    def add_snapshot(self, post_data: PostData, current_score: int, current_comments: int) -> None:
        """Add a new snapshot to the post data."""
        if post_data.snapshots is None:
            post_data.snapshots = []
        
        snapshot = PostSnapshot(
            timestamp=datetime.now(),
            score=current_score,
            num_comments=current_comments
        )
        post_data.snapshots.append(snapshot)
        
        # Keep only last 10 snapshots to prevent memory issues
        if len(post_data.snapshots) > 10:
            post_data.snapshots = post_data.snapshots[-10:]
    
    def calculate_upvote_rate_from_snapshots(self, post_data: PostData) -> float:
        """Calculate upvote rate from snapshots (latest - first) / elapsed minutes."""
        if not post_data.snapshots or len(post_data.snapshots) < 2:
            return 0.0
        
        first_snapshot = post_data.snapshots[0]
        latest_snapshot = post_data.snapshots[-1]
        
        time_diff = (latest_snapshot.timestamp - first_snapshot.timestamp).total_seconds() / 60
        if time_diff <= 0:
            return 0.0
        
        return (latest_snapshot.score - first_snapshot.score) / time_diff
    
    def calculate_moving_average_rate(self, post_data: PostData, window_size: int = 3) -> float:
        """Calculate moving average upvote rate over last N snapshots."""
        if not post_data.snapshots or len(post_data.snapshots) < 2:
            return 0.0
        
        # Use last window_size snapshots, or all if we have fewer
        snapshots_to_use = post_data.snapshots[-min(window_size, len(post_data.snapshots)):]
        
        if len(snapshots_to_use) < 2:
            return 0.0
        
        rates = []
        for i in range(1, len(snapshots_to_use)):
            time_diff = (snapshots_to_use[i].timestamp - snapshots_to_use[i-1].timestamp).total_seconds() / 60
            if time_diff > 0:
                rate = (snapshots_to_use[i].score - snapshots_to_use[i-1].score) / time_diff
                rates.append(rate)
        
        return sum(rates) / len(rates) if rates else 0.0
    
    def calculate_upvote_rate(self, post_data: PostData, current_score: int) -> float:
        """Calculate upvote rate (upvotes per minute) for a post - legacy method."""
        time_diff = (datetime.now() - post_data.last_checked).total_seconds() / 60
        if time_diff <= 0:
            return 0
        return (current_score - post_data.score) / time_diff
        
    def calculate_comment_rate(self, post_data: PostData, current_comments: int) -> float:
        """Calculate comment rate (comments per minute) for a post."""
        time_diff = (datetime.now() - post_data.last_checked).total_seconds() / 60
        if time_diff <= 0:
            return 0
        return (current_comments - post_data.comment_count) / time_diff
        
    def is_post_eligible(self, post, subreddit_config: Dict) -> bool:
        """Check if a post is eligible for tracking."""
        # Hardcoded blacklist of posts to skip (persistent Reddit hot posts)
        BLACKLISTED_POSTS = {
            '1njaxm7', '1njcxu8', '1nix2i1', '1niwlce', '1niw0dn', '1nir57q', 
            '1ninic3', '1niycja', '1nipgmv', '1nj7d5r', '1nihypp', '1niue0r', 
            '1nii8b4', '1nil1zq', '1niwiyb', '1nis1zd', '1nj00c4', '1niq9qn', 
            '1nj4mtn', '1nipkx8', '1nj0pee', '1nisoza', '1njbijq', '1njbre0'
        }
        
        # Skip blacklisted posts
        if post.id in BLACKLISTED_POSTS:
            return False
        
        post_age = datetime.now() - datetime.fromtimestamp(post.created_utc)
        
        # Check minimum age using subreddit-specific min_age
        if post_age < timedelta(minutes=subreddit_config['min_age']):
            return False
            
        # Check maximum age
        if post_age > timedelta(hours=POST_TRACKING['max_post_age_hours']):
            return False
            
        return True
        
    def process_post(self, post, subreddit_config: Dict) -> Optional[PostData]:
        """Process a single post and return PostData if it should be tracked."""
        if not self.is_post_eligible(post, subreddit_config):
            return None
            
        post_key = self.get_post_key(subreddit_config['name'], post.id)
        
        # Get post URL
        post_url = f"https://reddit.com{post.permalink}"
        
        # Check for image URL using comprehensive detection
        image_url = self.get_image_url(post)
        
        # Create or update post data
        if post_key in self.tracked_posts:
            # Update existing post
            post_data = self.tracked_posts[post_key]
            
            # Add new snapshot
            self.add_snapshot(post_data, post.score, post.num_comments)
            
            # Update basic data
            post_data.score = post.score
            post_data.comment_count = post.num_comments
            post_data.last_checked = datetime.now()
            
            # Calculate rates using snapshots
            upvote_rate = self.calculate_upvote_rate_from_snapshots(post_data)
            moving_avg_rate = self.calculate_moving_average_rate(post_data)
            post_data.upvote_rate = upvote_rate
            
            # Calculate comment rate (legacy method for now)
            comment_rate = self.calculate_comment_rate(post_data, post.num_comments)
            post_data.comment_rate = comment_rate
            
            # Dynamic threshold logic
            if not post_data.has_triggered and post_data.is_tracking:
                # Check if post exceeds follow-up threshold
                if upvote_rate >= subreddit_config['followup_threshold']:
                    self.log_rising_post(post_data, subreddit_config)
                    post_data.has_triggered = True
                    
        else:
            # Create new post data
            post_data = PostData(
                id=post.id,
                title=post.title,
                url=post_url,
                score=post.score,
                upvote_rate=0.0,
                comment_rate=0.0,
                created_utc=post.created_utc,
                subreddit=subreddit_config['name'],
                last_checked=datetime.now(),
                image_url=image_url,
                snapshots=[]
            )
            post_data.comment_count = post.num_comments
            
            # Add initial snapshot
            self.add_snapshot(post_data, post.score, post.num_comments)
            
            # Download image if present
            if image_url:
                image_path = self.download_image(image_url, post.id, subreddit_config['name'])
                post_data.image_path = image_path
                
            # Generate summary
            if SUMMARIZATION['enabled']:
                summary = self.generate_summary(post_data)
                post_data.summary = summary
                self.logger.info(f"Summary for post {post_data.id}: {summary}")
            
            # Create post package for every post with image (regardless of threshold)
            if post_data.image_path:
                self.create_post_package(post_data)
            
            # Check initial threshold to decide if we should start tracking
            if len(post_data.snapshots) >= 2:
                initial_rate = self.calculate_upvote_rate_from_snapshots(post_data)
                post_data.initial_rate = initial_rate
                
                if initial_rate >= subreddit_config['initial_threshold']:
                    post_data.is_tracking = True
                    self.logger.info(f"Started tracking post {post.id} with initial rate {initial_rate:.1f} upvotes/min")
                else:
                    # Remove from tracking if it doesn't meet initial threshold
                    return None
            
        return post_data
        
    def log_rising_post(self, post_data: PostData, subreddit_config: Dict):
        """Log a rising post that exceeds the threshold and create meme package."""
        moving_avg_rate = self.calculate_moving_average_rate(post_data)
        log_message = (
            f"RISING POST DETECTED in {subreddit_config['display_name']}!\n"
            f"  Title: {post_data.title}\n"
            f"  URL: {post_data.url}\n"
            f"  Current Score: {post_data.score}\n"
            f"  Upvote Rate: {post_data.upvote_rate:.1f} upvotes/min\n"
            f"  Moving Avg Rate: {moving_avg_rate:.1f} upvotes/min\n"
            f"  Comment Rate: {post_data.comment_rate:.1f} comments/min\n"
            f"  Initial Rate: {post_data.initial_rate:.1f} upvotes/min\n"
            f"  Follow-up Threshold: {subreddit_config['followup_threshold']} upvotes/min\n"
            f"  Snapshots: {len(post_data.snapshots) if post_data.snapshots else 0}\n"
        )
        
        # Add image information if present
        if post_data.image_url:
            log_message += f"  Image URL: {post_data.image_url}\n"
        if post_data.image_path:
            log_message += f"  Image Saved: {post_data.image_path}\n"
            
        # Add summary if present
        if post_data.summary:
            log_message += f"  Summary: {post_data.summary}\n"
            
        log_message += f"  {'='*50}"
        
        self.logger.info(log_message)
        
        # Create complete meme package if enabled
        if MEME_PACKAGES['enabled']:
            package_path = self.create_meme_package(post_data)
            if package_path:
                self.logger.info(f"Meme package created successfully: {package_path}")
            else:
                self.logger.warning(f"Failed to create meme package for post {post_data.id}")
        else:
            self.logger.info("Meme package creation is disabled")
        
    def monitor_subreddit(self, subreddit_config: Dict):
        """Monitor a specific subreddit for rising posts."""
        subreddit_name = subreddit_config['name']
        self.logger.info(f"Starting monitoring for r/{subreddit_name} - tracking RISING posts only (not already hot)")
        
        # Wait 30 seconds before starting to process posts (let the bot settle)
        self.logger.info(f"⏳ Waiting 30 seconds before starting to track posts...")
        time.sleep(30)
        self.logger.info(f"🚀 r/{subreddit_name} monitoring is now ACTIVE - looking for rising posts!")
        
        while self.running:
            try:
                # Get the subreddit
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get rising posts only (not already hot posts)
                self.logger.info(f"🔍 Checking r/{subreddit_name} for rising posts...")
                posts = subreddit.rising(limit=10)
                
                posts_checked = 0
                posts_processed = 0
                posts_skipped = 0
                
                for post in posts:
                    if not self.running:
                        break
                    
                    posts_checked += 1
                    
                    # Only process posts that are actually rising (not already established hot posts)
                    # Skip posts that are too old or already very popular
                    post_age = datetime.now() - datetime.fromtimestamp(post.created_utc)
                    if post_age > timedelta(hours=2):  # Skip posts older than 2 hours
                        posts_skipped += 1
                        continue
                    if post.score > 1000:  # Skip posts that are already very popular
                        posts_skipped += 1
                        continue
                        
                    post_data = self.process_post(post, subreddit_config)
                    if post_data:
                        post_key = self.get_post_key(subreddit_name, post.id)
                        self.tracked_posts[post_key] = post_data
                        posts_processed += 1
                
                # Log status summary
                self.logger.info(f"📊 r/{subreddit_name} check complete: {posts_checked} posts checked, {posts_processed} processed, {posts_skipped} skipped")
                        
                # Clean up old posts
                self.cleanup_old_posts(subreddit_name)
                
                # Wait for next poll
                self.logger.info(f"⏰ Waiting {subreddit_config['poll_interval']} seconds before next check...")
                time.sleep(subreddit_config['poll_interval'])
                
            except Exception as e:
                self.logger.error(f"Error monitoring r/{subreddit_name}: {e}")
                time.sleep(30)  # Wait before retrying
                
    def cleanup_old_posts(self, subreddit_name: str):
        """Remove old posts from tracking to prevent memory issues."""
        current_time = datetime.now()
        max_age = timedelta(hours=POST_TRACKING['max_post_age_hours'])
        
        # Get posts for this subreddit
        subreddit_posts = {
            k: v for k, v in self.tracked_posts.items() 
            if v.subreddit == subreddit_name
        }
        
        # Remove old posts
        for post_key, post_data in list(subreddit_posts.items()):
            post_age = current_time - datetime.fromtimestamp(post_data.created_utc)
            if post_age > max_age:
                del self.tracked_posts[post_key]
                
        # Limit total posts per subreddit
        if len(subreddit_posts) > POST_TRACKING['max_posts_per_subreddit']:
            # Sort by creation time and keep newest
            sorted_posts = sorted(
                subreddit_posts.items(),
                key=lambda x: x[1].created_utc,
                reverse=True
            )
            
            # Remove oldest posts
            for post_key, _ in sorted_posts[POST_TRACKING['max_posts_per_subreddit']:]:
                if post_key in self.tracked_posts:
                    del self.tracked_posts[post_key]
                    
    def is_image_url(self, url: str) -> bool:
        """Check if URL points to an image."""
        if not url:
            return False
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        return any(path.endswith(ext) for ext in IMAGE_PROCESSING['supported_formats'])
        
    def get_image_url(self, post) -> Optional[str]:
        """Extract image URL from Reddit post using multiple methods."""
        if not post:
            return None
            
        # Method 1: Direct image URL in post.url
        if hasattr(post, 'url') and self.is_image_url(post.url):
            return post.url
            
        # Method 2: Check for Reddit's preview images
        if hasattr(post, 'preview') and post.preview:
            try:
                # Get the highest resolution preview image
                if 'images' in post.preview and post.preview['images']:
                    source = post.preview['images'][0].get('source', {})
                    if 'url' in source:
                        # Decode HTML entities in URL
                        import html
                        return html.unescape(source['url'])
            except Exception as e:
                self.logger.debug(f"Error parsing preview images: {e}")
                
        # Method 3: Check for gallery posts (multiple images)
        if hasattr(post, 'is_gallery') and post.is_gallery:
            try:
                if hasattr(post, 'gallery_data') and post.gallery_data:
                    # For gallery posts, get the first image
                    items = post.gallery_data.get('items', [])
                    if items and 'media_id' in items[0]:
                        media_id = items[0]['media_id']
                        # Try to construct image URL
                        return f"https://i.redd.it/{media_id}.jpg"
            except Exception as e:
                self.logger.debug(f"Error parsing gallery data: {e}")
                
        # Method 4: Check for imgur links and other image hosts
        if hasattr(post, 'url') and post.url:
            url = post.url.lower()
            # Handle imgur links
            if 'imgur.com' in url:
                # Convert imgur album/single links to direct image URLs
                if '/a/' in url or '/gallery/' in url:
                    # Skip albums for now, focus on single images
                    pass
                elif not url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    # Try to get direct image URL
                    return f"{url}.jpg"
                else:
                    return post.url
                    
        # Method 5: Check for other common image hosting services
        if hasattr(post, 'url') and post.url:
            url = post.url.lower()
            if any(host in url for host in ['i.redd.it', 'preview.redd.it', 'external-preview.redd.it']):
                return post.url
                
        return None
        
    def download_image(self, image_url: str, post_id: str, subreddit: str) -> Optional[str]:
        """Download image from URL and save to images folder."""
        if not IMAGE_PROCESSING['download_images'] or not image_url:
            return None
            
        # Check if it's a valid image URL (more flexible check)
        if not (self.is_image_url(image_url) or 'imgur.com' in image_url.lower() or 'i.redd.it' in image_url.lower()):
            return None
            
        try:
            # Create images directory if it doesn't exist
            images_dir = Path(IMAGE_PROCESSING['images_folder'])
            images_dir.mkdir(exist_ok=True)
            
            # Generate filename
            file_ext = Path(urlparse(image_url).path).suffix or '.jpg'
            filename = f"{subreddit}_{post_id}_{int(time.time())}{file_ext}"
            file_path = images_dir / filename
            
            # Download image
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check file size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > IMAGE_PROCESSING['max_image_size_mb'] * 1024 * 1024:
                self.logger.warning(f"Image too large ({content_length} bytes), skipping: {image_url}")
                return None
                
            # Save image
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Verify it's a valid image
            try:
                with Image.open(file_path) as img:
                    img.verify()
                self.logger.info(f"Downloaded image: {file_path}")
                return str(file_path)
            except Exception as e:
                self.logger.warning(f"Invalid image file, deleting: {file_path} - {e}")
                os.remove(file_path)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to download image {image_url}: {e}")
            return None
    
    def create_human_readable_folder_name(self, title: str, post_id: str) -> str:
        """Create a human-readable folder name from post title."""
        # Clean the title
        clean_title = title.lower()
        # Remove special characters and replace spaces with hyphens
        clean_title = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in clean_title)
        # Replace multiple spaces with single space, then replace spaces with hyphens
        clean_title = '-'.join(clean_title.split())
        # Limit length and add post ID
        if len(clean_title) > 50:
            clean_title = clean_title[:50]
        # Add post ID to ensure uniqueness
        return f"{clean_title}-{post_id}"
    
    def create_post_package(self, post_data: PostData) -> Optional[str]:
        """Create a complete package for every post with image, regardless of threshold."""
        if not post_data.image_path or not os.path.exists(post_data.image_path):
            return None
            
        try:
            # Create packages directory
            packages_folder = MEME_PACKAGES['packages_folder']
            packages_dir = Path(packages_folder)
            packages_dir.mkdir(exist_ok=True)
            
            # Create human-readable folder name
            folder_name = self.create_human_readable_folder_name(post_data.title, post_data.id)
            meme_dir = packages_dir / folder_name
            
            # Check if folder already exists (avoid duplicates)
            if meme_dir.exists():
                self.logger.debug(f"Package already exists for post {post_data.id}, skipping")
                return str(meme_dir)
            
            meme_dir.mkdir(exist_ok=True)
            
            # 1. Copy image to package
            image_filename = Path(post_data.image_path).name
            meme_image_path = meme_dir / image_filename
            shutil.copy2(post_data.image_path, meme_image_path)
            
            # 2. Save main meme description
            description_file = meme_dir / "meme_description.txt"
            with open(description_file, 'w', encoding='utf-8') as f:
                f.write(f"""MEME TOKEN DESCRIPTION
{'='*50}

Post Details:
- Title: {post_data.title}
- Subreddit: r/{post_data.subreddit}
- Post ID: {post_data.id}
- URL: {post_data.url}
- Score: {post_data.score}
- Comments: {post_data.comment_count}
- Created: {datetime.fromtimestamp(post_data.created_utc).strftime('%Y-%m-%d %H:%M:%S')}
- Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Meme Description:
{post_data.summary or 'No description generated'}

Image Information:
- Original URL: {post_data.image_url or 'No image'}
- Local Path: {post_data.image_path or 'No image downloaded'}

Token Metadata Ready: ✅
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}
""")
            
            # 3. Save detailed metadata JSON
            metadata = {
                "post_id": post_data.id,
                "title": post_data.title,
                "subreddit": post_data.subreddit,
                "url": post_data.url,
                "score": post_data.score,
                "comments": post_data.comment_count,
                "created_utc": post_data.created_utc,
                "created_human": datetime.fromtimestamp(post_data.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                "image_url": post_data.image_url,
                "image_local_path": str(meme_image_path),
                "meme_description": post_data.summary,
                "upvote_rate": post_data.upvote_rate,
                "comment_rate": post_data.comment_rate,
                "processed_at": datetime.now().isoformat(),
                "package_created": datetime.now().isoformat(),
                "folder_name": folder_name
            }
            
            metadata_file = meme_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 4. Save URLs list
            urls_file = meme_dir / "urls.txt"
            with open(urls_file, 'w', encoding='utf-8') as f:
                f.write(f"""REDDIT POST URLS
{'='*30}
Reddit Post: {post_data.url}
Original Image: {post_data.image_url or 'No image'}
Local Image: {str(meme_image_path)}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
            
            # 5. Create README for the package
            readme_file = meme_dir / "README.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"""# Meme Package: {post_data.title[:50]}...

## Files in this package:
- `meme_description.txt` - Main meme description for token metadata
- `metadata.json` - Complete post metadata in JSON format
- `urls.txt` - All relevant URLs
- `README.md` - This file
- `{image_filename}` - Downloaded image

## Meme Description:
{post_data.summary or 'No description generated'}

## Quick Stats:
- **Subreddit**: r/{post_data.subreddit}
- **Score**: {post_data.score}
- **Comments**: {post_data.comment_count}
- **Upvote Rate**: {post_data.upvote_rate:.1f} upvotes/min
- **Comment Rate**: {post_data.comment_rate:.1f} comments/min
- **Created**: {datetime.fromtimestamp(post_data.created_utc).strftime('%Y-%m-%d %H:%M:%S')}

## For Meme Token App:
This package contains everything needed to generate a meme token:
- Image file ready for processing
- AI-generated description
- Complete metadata in JSON format
- All relevant URLs

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
            
            self.logger.info(f"Created post package: {meme_dir}")
            return str(meme_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to create post package for {post_data.id}: {e}")
            return None
            
    def generate_summary(self, post_data: PostData) -> Optional[str]:
        """Generate witty, sarcastic meme-style description of the post."""
        if not SUMMARIZATION['enabled']:
            return None
            
        try:
            # Prepare content for description generation
            content = f"Title: {post_data.title}\n"
            if post_data.image_url:
                content += f"Image URL: {post_data.image_url}\n"
            content += f"Subreddit: r/{post_data.subreddit}\n"
            content += f"Score: {post_data.score}\n"
            content += f"Upvote Rate: {post_data.upvote_rate:.1f} upvotes/min"
            
            # Generate witty description using OpenAI
            response = self.openai_client.chat.completions.create(
                model=SUMMARIZATION['model'],
                messages=[
                    {"role": "system", "content": "You are a trolling, mocking observer who sounds like a mix of Ricky Gervais and Steve Carell from The Office. Generate a punchy, human-style description that MOCKS the Reddit post, don't explain it. Keep it 1-2 sentences maximum, only use 2 when absolutely needed. Like something a fed-up, smart, smug person would mutter while scrolling Reddit. Don't explain the situation or picture, just mock it. Small grammar mistakes are okay, as long as it still reads like a real human. Be witty and humorous, use internet slang and meme language when appropriate. Make it something that could go viral or become a meme token. Focus on trolling and mocking the absurdity. No emojis, minimal punctuation. Example: 'ah the sweet smell of bankruptcy ruining people's dreams'"},
                    {"role": "user", "content": f"Create a short, punchy description of this Reddit post:\n\n{content}"}
                ],
                max_tokens=SUMMARIZATION['max_tokens'],
                temperature=SUMMARIZATION['temperature']
            )
            
            summary = response.choices[0].message.content.strip()
            self.logger.info(f"Generated witty description for post {post_data.id}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate description for post {post_data.id}: {e}")
            return None
            
    def create_meme_package(self, post_data: PostData) -> Optional[str]:
        """Create a complete meme package with all metadata and files."""
        if not MEME_PACKAGES['enabled']:
            return None
            
        try:
            # Create meme package directory
            packages_folder = MEME_PACKAGES['packages_folder']
            if MEME_PACKAGES['include_timestamp']:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                meme_dir = Path(packages_folder) / f"{post_data.subreddit}_{post_data.id}_{timestamp}"
            else:
                meme_dir = Path(packages_folder) / f"{post_data.subreddit}_{post_data.id}"
            meme_dir.mkdir(parents=True, exist_ok=True)
            
            # 1. Save main meme description
            description_file = meme_dir / "meme_description.txt"
            with open(description_file, 'w', encoding='utf-8') as f:
                f.write(f"""MEME TOKEN DESCRIPTION
{'='*50}

Post Details:
- Title: {post_data.title}
- Subreddit: r/{post_data.subreddit}
- Post ID: {post_data.id}
- URL: {post_data.url}
- Score: {post_data.score}
- Comments: {post_data.comment_count}
- Created: {datetime.fromtimestamp(post_data.created_utc).strftime('%Y-%m-%d %H:%M:%S')}
- Detected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Meme Description:
{post_data.summary or 'No description generated'}

Image Information:
- Original URL: {post_data.image_url or 'No image'}
- Local Path: {post_data.image_path or 'No image downloaded'}

Token Metadata Ready: ✅
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}
""")
            
            # 2. Save detailed metadata JSON
            metadata = {
                "post_id": post_data.id,
                "title": post_data.title,
                "subreddit": post_data.subreddit,
                "url": post_data.url,
                "score": post_data.score,
                "comments": post_data.comment_count,
                "created_utc": post_data.created_utc,
                "created_human": datetime.fromtimestamp(post_data.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                "image_url": post_data.image_url,
                "image_local_path": post_data.image_path,
                "meme_description": post_data.summary,
                "upvote_rate": post_data.upvote_rate,
                "comment_rate": post_data.comment_rate,
                "detected_at": datetime.now().isoformat(),
                "package_created": datetime.now().isoformat()
            }
            
            metadata_file = meme_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 3. Save URLs list
            urls_file = meme_dir / "urls.txt"
            with open(urls_file, 'w', encoding='utf-8') as f:
                f.write(f"""REDDIT POST URLS
{'='*30}
Reddit Post: {post_data.url}
Original Image: {post_data.image_url or 'No image'}
Local Image: {post_data.image_path or 'No image downloaded'}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
            
            # 4. Copy image to meme package if it exists
            if post_data.image_path and os.path.exists(post_data.image_path):
                image_filename = Path(post_data.image_path).name
                meme_image_path = meme_dir / image_filename
                shutil.copy2(post_data.image_path, meme_image_path)
                self.logger.info(f"Image copied to: {meme_image_path}")
            
            # 5. Create README for the package
            readme_file = meme_dir / "README.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"""# Meme Package: {post_data.title[:50]}...

## Files in this package:
- `meme_description.txt` - Main meme description for token metadata
- `metadata.json` - Complete post metadata in JSON format
- `urls.txt` - All relevant URLs
- `README.md` - This file
- `{Path(post_data.image_path).name if post_data.image_path else 'no_image'}` - Downloaded image (if available)

## Meme Description:
{post_data.summary or 'No description generated'}

## Quick Stats:
- **Subreddit**: r/{post_data.subreddit}
- **Score**: {post_data.score}
- **Comments**: {post_data.comment_count}
- **Upvote Rate**: {post_data.upvote_rate:.1f} upvotes/min
- **Comment Rate**: {post_data.comment_rate:.1f} comments/min
- **Created**: {datetime.fromtimestamp(post_data.created_utc).strftime('%Y-%m-%d %H:%M:%S')}

Generated by Meme Material Radar
""")
            
            self.logger.info(f"Complete meme package saved to: {meme_dir}")
            self.logger.info(f"Files created: meme_description.txt, metadata.json, urls.txt, README.md")
            if post_data.image_path:
                self.logger.info(f"Image included: {Path(post_data.image_path).name}")
            
            return str(meme_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to create meme package for post {post_data.id}: {e}")
            return None
            
    def start_monitoring(self):
        """Start monitoring all configured subreddits."""
        self.running = True
        self.logger.info("Starting Meme Material Radar - tracking RISING posts only...")
        
        # Create threads for each subreddit
        threads = []
        for subreddit_name, subreddit_config in SUBREDDITS.items():
            thread = threading.Thread(
                target=self.monitor_subreddit,
                args=(subreddit_config,),
                name=f"Monitor-{subreddit_name}"
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
            
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.running = False
            
        # Wait for threads to finish
        for thread in threads:
            thread.join(timeout=5)
            
        self.logger.info("Meme Material Radar stopped.")


def main():
    """Main entry point for the application."""
    print("Meme Material Radar - Reddit Post Monitoring Tool")
    print("=" * 50)
    
    try:
        monitor = RedditMonitor()
        monitor.start_monitoring()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
