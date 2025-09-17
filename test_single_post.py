#!/usr/bin/env python3
"""
Test script for single Reddit post processing.
Tests image downloading and AI summarization on one post.
"""

import os
import sys
import time
from datetime import datetime

import praw
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import IMAGE_PROCESSING, SUMMARIZATION
from src.meme_radar import RedditMonitor

def test_single_post():
    """Test image downloading and summarization on a single Reddit post."""
    print("🧪 Testing Single Post Processing")
    print("=" * 50)
    
    # Load environment variables
    env_path = os.path.join('config', '.env')
    load_dotenv(env_path)
    
    # Initialize Reddit API
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            username=os.getenv('REDDIT_USERNAME'),
            password=os.getenv('REDDIT_PASSWORD'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
        print("✅ Connected to Reddit API")
    except Exception as e:
        print(f"❌ Failed to connect to Reddit API: {e}")
        return
    
    # Initialize OpenAI
    try:
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')
        print("✅ OpenAI API configured")
    except Exception as e:
        print(f"❌ Failed to configure OpenAI: {e}")
        return
    
    # Create monitor instance for helper methods
    monitor = RedditMonitor()
    
    # Get a single post from r/news (looking for one with an image)
    print("\n🔍 Searching for a post with an image...")
    
    try:
        subreddit = reddit.subreddit('news')
        posts = subreddit.hot(limit=20)
        
        test_post = None
        for post in posts:
            # Check if post has an image
            if hasattr(post, 'url') and monitor.is_image_url(post.url):
                test_post = post
                break
        
        if not test_post:
            print("❌ No image posts found in r/news. Trying r/pics...")
            subreddit = reddit.subreddit('pics')
            posts = subreddit.hot(limit=10)
            
            for post in posts:
                if hasattr(post, 'url') and monitor.is_image_url(post.url):
                    test_post = post
                    break
        
        if not test_post:
            print("❌ No image posts found. Using any post for testing...")
            subreddit = reddit.subreddit('news')
            test_post = next(subreddit.hot(limit=1))
        
        print(f"✅ Found test post: {test_post.title[:100]}...")
        
    except Exception as e:
        print(f"❌ Failed to get test post: {e}")
        return
    
    # Process the post
    print(f"\n📝 Processing post: {test_post.title}")
    print(f"🔗 URL: https://reddit.com{test_post.permalink}")
    print(f"📊 Score: {test_post.score}")
    print(f"💬 Comments: {test_post.num_comments}")
    
    # Check for image
    image_url = None
    if hasattr(test_post, 'url') and monitor.is_image_url(test_post.url):
        image_url = test_post.url
        print(f"🖼️  Image URL: {image_url}")
        
        # Test image download
        print("\n⬇️  Testing image download...")
        image_path = monitor.download_image(image_url, test_post.id, 'test')
        if image_path:
            print(f"✅ Image downloaded: {image_path}")
            print(f"📁 File size: {os.path.getsize(image_path)} bytes")
        else:
            print("❌ Image download failed")
    else:
        print("ℹ️  No image found in this post")
    
    # Test AI summarization
    print("\n🤖 Testing AI summarization...")
    
    # Create a mock PostData object
    from src.meme_radar import PostData
    post_data = PostData(
        id=test_post.id,
        title=test_post.title,
        url=f"https://reddit.com{test_post.permalink}",
        score=test_post.score,
        upvote_rate=0.0,
        comment_rate=0.0,
        created_utc=test_post.created_utc,
        subreddit='test',
        last_checked=datetime.now(),
        image_url=image_url,
        image_path=image_path if 'image_path' in locals() else None
    )
    
    summary = monitor.generate_summary(post_data)
    if summary:
        print(f"✅ Summary generated:")
        print(f"📄 {summary}")
    else:
        print("❌ Summary generation failed")
    
    # Test logging
    print("\n📋 Testing enhanced logging...")
    monitor.log_rising_post(post_data, {'display_name': 'r/test', 'upvote_rate_threshold': 10})
    
    print("\n🎉 Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_single_post()
