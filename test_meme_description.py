#!/usr/bin/env python3
"""
Test script for meme-style description generation.
Creates witty, meme-flavored descriptions for Reddit posts that could be used for meme tokens.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import praw
from dotenv import load_dotenv
import openai

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def generate_meme_description(post_title, subreddit, score, image_url=None):
    """Generate a meme-style description using OpenAI."""
    try:
        # Prepare context for meme generation
        context = f"""
Post Title: {post_title}
Subreddit: r/{subreddit}
Score: {score}
"""
        
        if image_url:
            context += f"Image URL: {image_url}"
        
        # Create a meme-focused prompt
        prompt = f"""
You are a meme culture expert and crypto token creator. Analyze this Reddit post and create a witty, meme-flavored description that captures the essence of what's happening in a way that could become a viral meme or inspire a meme coin.

The description should be:
- 2-3 sentences maximum
- Witty and humorous
- Capture the cultural moment or absurdity
- Use internet slang and meme language when appropriate
- Be something that could go viral or become a meme token
- Focus on the "vibe" or "energy" of the situation

Post Context:
{context}

Generate a meme-worthy description:
"""
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a meme culture expert who creates viral, witty descriptions for crypto tokens and memes. You understand internet culture, slang, and what makes content go viral."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.8  # Higher creativity for meme content
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"❌ Failed to generate meme description: {e}")
        return f"🔥 {post_title} - This post is absolutely sending it! 💀"

def download_image(image_url, post_id, subreddit):
    """Download image and return the path."""
    try:
        import requests
        from PIL import Image
        
        # Create images directory
        images_dir = Path("images")
        images_dir.mkdir(exist_ok=True)
        
        # Generate filename
        file_ext = Path(image_url).suffix or '.jpg'
        filename = f"{subreddit}_{post_id}_{int(time.time())}{file_ext}"
        file_path = images_dir / filename
        
        # Download image
        response = requests.get(image_url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Save image
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify it's a valid image
        with Image.open(file_path) as img:
            img.verify()
        
        return str(file_path)
        
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return None

def save_meme_package(post_data, meme_description, image_path):
    """Save the complete meme package (description + image) in organized folders."""
    try:
        # Create meme package directory
        meme_dir = Path("meme_packages") / f"{post_data['subreddit']}_{post_data['id']}"
        meme_dir.mkdir(parents=True, exist_ok=True)
        
        # Save meme description
        description_file = meme_dir / "meme_description.txt"
        with open(description_file, 'w', encoding='utf-8') as f:
            f.write(f"""MEME TOKEN DESCRIPTION
{'='*50}

Post Details:
- Title: {post_data['title']}
- Subreddit: r/{post_data['subreddit']}
- Post ID: {post_data['id']}
- URL: {post_data['url']}
- Score: {post_data['score']}
- Created: {post_data['created']}

Meme Description:
{meme_description}

Image Information:
- Original URL: {post_data.get('image_url', 'No image')}
- Local Path: {image_path or 'No image downloaded'}

Token Metadata Ready: ✅
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}
""")
        
        # Copy image to meme package if it exists
        if image_path and os.path.exists(image_path):
            import shutil
            image_filename = Path(image_path).name
            meme_image_path = meme_dir / image_filename
            shutil.copy2(image_path, meme_image_path)
            print(f"📁 Image copied to: {meme_image_path}")
        
        print(f"📁 Meme package saved to: {meme_dir}")
        print(f"📄 Description saved to: {description_file}")
        
        return str(meme_dir)
        
    except Exception as e:
        print(f"❌ Failed to save meme package: {e}")
        return None

def test_meme_description():
    """Test meme description generation on a single Reddit post."""
    print("🎭 Testing Meme Description Generation")
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
        openai.api_key = os.getenv('OPENAI_API_KEY')
        print("✅ OpenAI API configured")
    except Exception as e:
        print(f"❌ Failed to configure OpenAI: {e}")
        return
    
    # Get a trending post (preferably with image)
    print("\n🔍 Finding a trending post for meme generation...")
    
    try:
        # Try r/news first for news content
        subreddit = reddit.subreddit('news')
        posts = subreddit.hot(limit=10)
        
        test_post = None
        for post in posts:
            if post.score > 1000:  # Look for highly upvoted posts
                test_post = post
                break
        
        if not test_post:
            # Fallback to r/pics for image content
            subreddit = reddit.subreddit('pics')
            test_post = next(subreddit.hot(limit=1))
        
        print(f"✅ Found test post: {test_post.title[:80]}...")
        
    except Exception as e:
        print(f"❌ Failed to get test post: {e}")
        return
    
    # Prepare post data
    post_data = {
        'id': test_post.id,
        'title': test_post.title,
        'subreddit': test_post.subreddit.display_name,
        'url': f"https://reddit.com{test_post.permalink}",
        'score': test_post.score,
        'created': datetime.fromtimestamp(test_post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
        'image_url': test_post.url if hasattr(test_post, 'url') else None
    }
    
    print(f"\n📝 Post Details:")
    print(f"   Title: {post_data['title']}")
    print(f"   Subreddit: r/{post_data['subreddit']}")
    print(f"   Score: {post_data['score']}")
    print(f"   URL: {post_data['url']}")
    
    # Check for image
    image_path = None
    if post_data['image_url'] and any(post_data['image_url'].lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        print(f"   🖼️  Image: {post_data['image_url']}")
        print("\n⬇️  Downloading image...")
        image_path = download_image(post_data['image_url'], post_data['id'], post_data['subreddit'])
        if image_path:
            print(f"✅ Image downloaded: {image_path}")
    else:
        print("   ℹ️  No image found")
    
    # Generate meme description
    print("\n🎭 Generating meme description...")
    meme_description = generate_meme_description(
        post_data['title'],
        post_data['subreddit'],
        post_data['score'],
        post_data['image_url']
    )
    
    if meme_description:
        print(f"✅ Meme description generated:")
        print(f"🎯 {meme_description}")
    else:
        print("❌ Failed to generate meme description")
        return
    
    # Save complete meme package
    print("\n💾 Saving meme package...")
    package_path = save_meme_package(post_data, meme_description, image_path)
    
    if package_path:
        print(f"✅ Meme package created successfully!")
        print(f"📁 Location: {package_path}")
        print(f"📄 Contains: meme_description.txt + image file")
    else:
        print("❌ Failed to save meme package")
    
    print("\n🎉 Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_meme_description()
