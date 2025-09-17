#!/usr/bin/env python3
"""
Complete test for meme package generation with all metadata, images, and descriptions.
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
    """Generate a one-line, punchy description using OpenAI."""
    try:
        context = f"""
Post Title: {post_title}
Subreddit: r/{subreddit}
Score: {score}
"""
        
        if image_url:
            context += f"Image URL: {image_url}"
        
        prompt = f"""
Generate a very short, punchy, human-style description of the Reddit post. Keep it one line, like something a fed-up, smart, smug person would mutter while scrolling Reddit. Don't add extra narrative or jokes unless they naturally fit in one line. Small grammar mistakes are okay, as long as it still reads like a real human. Basically, just capture the essence or absurdity of the post in one short sentence.

If the post is politically leaning or involves political topics, add a subtle center-right perspective when appropriate - never leftist. Keep it natural and not forced, only when the subject matter allows for it.

Post Context:
{context}

Generate a one-line description:
"""
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a smart, smug person scrolling Reddit who mutters short, punchy observations. You capture the essence or absurdity of posts in one line. Small grammar mistakes are fine. Keep it human and direct. When political topics arise, you lean center-right but keep it subtle and natural - never leftist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"❌ Failed to generate meme description: {e}")
        return f"another day another thing that makes you question everything"

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

def save_complete_meme_package(post_data, meme_description, image_path):
    """Save the complete meme package with all metadata."""
    try:
        # Create meme package directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        meme_dir = Path("meme_packages") / f"{post_data['subreddit']}_{post_data['id']}_{timestamp}"
        meme_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Save main meme description
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
- Comments: {post_data.get('comments', 'N/A')}
- Created: {post_data['created']}
- Detected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Meme Description:
{meme_description}

Image Information:
- Original URL: {post_data.get('image_url', 'No image')}
- Local Path: {image_path or 'No image downloaded'}

Token Metadata Ready: ✅
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}
""")
        
        # 2. Save detailed metadata JSON
        import json
        metadata = {
            "post_id": post_data['id'],
            "title": post_data['title'],
            "subreddit": post_data['subreddit'],
            "url": post_data['url'],
            "score": post_data['score'],
            "comments": post_data.get('comments', 0),
            "created_utc": post_data.get('created_utc', 0),
            "created_human": post_data['created'],
            "image_url": post_data.get('image_url'),
            "image_local_path": image_path,
            "meme_description": meme_description,
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
Reddit Post: {post_data['url']}
Original Image: {post_data.get('image_url', 'No image')}
Local Image: {image_path or 'No image downloaded'}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
        
        # 4. Copy image to meme package if it exists
        if image_path and os.path.exists(image_path):
            import shutil
            image_filename = Path(image_path).name
            meme_image_path = meme_dir / image_filename
            shutil.copy2(image_path, meme_image_path)
            print(f"📁 Image copied to: {meme_image_path}")
        
        # 5. Create README for the package
        readme_file = meme_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(f"""# Meme Package: {post_data['title'][:50]}...

## Files in this package:
- `meme_description.txt` - Main meme description for token metadata
- `metadata.json` - Complete post metadata in JSON format
- `urls.txt` - All relevant URLs
- `README.md` - This file
- `{Path(image_path).name if image_path else 'no_image'}` - Downloaded image (if available)

## Meme Description:
{meme_description}

## Quick Stats:
- **Subreddit**: r/{post_data['subreddit']}
- **Score**: {post_data['score']}
- **Comments**: {post_data.get('comments', 'N/A')}
- **Created**: {post_data['created']}

Generated by Meme Material Radar
""")
        
        print(f"📁 Complete meme package saved to: {meme_dir}")
        print(f"📄 Files created:")
        print(f"   - meme_description.txt")
        print(f"   - metadata.json")
        print(f"   - urls.txt")
        print(f"   - README.md")
        if image_path:
            print(f"   - {Path(image_path).name}")
        
        return str(meme_dir)
        
    except Exception as e:
        print(f"❌ Failed to save complete meme package: {e}")
        return None

def test_complete_package():
    """Test complete meme package generation."""
    print("🎭 Testing Complete Meme Package Generation")
    print("=" * 60)
    
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
    
    # Find a post with an image
    print("\n🔍 Finding a post with an image...")
    
    try:
        # Try r/pics for image content
        subreddit = reddit.subreddit('pics')
        posts = subreddit.hot(limit=10)
        
        test_post = None
        for post in posts:
            if hasattr(post, 'url') and any(post.url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                test_post = post
                break
        
        if not test_post:
            # Fallback to any post
            subreddit = reddit.subreddit('news')
            test_post = next(subreddit.hot(limit=1))
        
        print(f"✅ Found test post: {test_post.title[:80]}...")
        
    except Exception as e:
        print(f"❌ Failed to get test post: {e}")
        return
    
    # Prepare complete post data
    post_data = {
        'id': test_post.id,
        'title': test_post.title,
        'subreddit': test_post.subreddit.display_name,
        'url': f"https://reddit.com{test_post.permalink}",
        'score': test_post.score,
        'comments': test_post.num_comments,
        'created': datetime.fromtimestamp(test_post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
        'created_utc': test_post.created_utc,
        'image_url': test_post.url if hasattr(test_post, 'url') else None
    }
    
    print(f"\n📝 Post Details:")
    print(f"   Title: {post_data['title']}")
    print(f"   Subreddit: r/{post_data['subreddit']}")
    print(f"   Score: {post_data['score']}")
    print(f"   Comments: {post_data['comments']}")
    print(f"   URL: {post_data['url']}")
    
    # Download image
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
        print(f"✅ Meme description: {meme_description}")
    else:
        print("❌ Failed to generate meme description")
        return
    
    # Save complete meme package
    print("\n💾 Saving complete meme package...")
    package_path = save_complete_meme_package(post_data, meme_description, image_path)
    
    if package_path:
        print(f"\n✅ Complete meme package created successfully!")
        print(f"📁 Location: {package_path}")
        print(f"📦 Contains all metadata, images, descriptions, and URLs")
    else:
        print("❌ Failed to save complete meme package")
    
    print("\n🎉 Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_package()