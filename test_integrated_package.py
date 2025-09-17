#!/usr/bin/env python3
"""
Test script to verify the integrated meme package creation in the main monitoring system.
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.meme_radar import RedditMonitor, PostData

def test_meme_package_creation():
    """Test the integrated meme package creation functionality."""
    print("🧪 Testing Integrated Meme Package Creation")
    print("=" * 60)
    
    # Create a mock PostData object
    post_data = PostData(
        id="test123",
        title="Test Post: Something that would definitely go viral",
        url="https://reddit.com/r/test/comments/test123/",
        score=1500,
        upvote_rate=25.5,
        comment_rate=8.2,
        created_utc=datetime.now().timestamp(),
        subreddit="test",
        last_checked=datetime.now(),
        comment_count=45,
        image_url="https://example.com/test_image.jpg",
        image_path="images/test_123_1234567890.jpg",
        summary="This is a test description that would definitely make people laugh and share it everywhere."
    )
    
    # Create monitor instance
    monitor = RedditMonitor()
    
    print(f"📝 Test Post Data:")
    print(f"   Title: {post_data.title}")
    print(f"   Subreddit: r/{post_data.subreddit}")
    print(f"   Score: {post_data.score}")
    print(f"   Upvote Rate: {post_data.upvote_rate:.1f} upvotes/min")
    print(f"   Summary: {post_data.summary}")
    
    # Test package creation
    print(f"\n🎁 Testing meme package creation...")
    package_path = monitor.create_meme_package(post_data)
    
    if package_path:
        print(f"✅ SUCCESS! Meme package created at: {package_path}")
        print(f"📁 Package should contain:")
        print(f"   - meme_description.txt")
        print(f"   - metadata.json")
        print(f"   - urls.txt")
        print(f"   - README.md")
        print(f"   - test_123_1234567890.jpg (if image exists)")
    else:
        print(f"❌ FAILED! Could not create meme package")
    
    print(f"\n🎉 Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_meme_package_creation()
