#!/usr/bin/env python3
"""
Test script to try different types of Reddit posts for meme descriptions.
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
        # Prepare context for meme generation
        context = f"""
Post Title: {post_title}
Subreddit: r/{subreddit}
Score: {score}
"""
        
        if image_url:
            context += f"Image URL: {image_url}"
        
        # Create a short, punchy prompt
        prompt = f"""
Generate a very short, punchy, human-style description of the Reddit post. Keep it one line, like something a fed-up, smart, smug person would mutter while scrolling Reddit. Don't add extra narrative or jokes unless they naturally fit in one line. Small grammar mistakes are okay, as long as it still reads like a real human. Basically, just capture the essence or absurdity of the post in one short sentence.

Post Context:
{context}

Generate a one-line description:
"""
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a smart, smug person scrolling Reddit who mutters short, punchy observations. You capture the essence or absurdity of posts in one line. Small grammar mistakes are fine. Keep it human and direct."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,  # Very short
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"❌ Failed to generate meme description: {e}")
        return f"another day another thing that makes you question everything"

def test_different_posts():
    """Test meme description generation on different types of Reddit posts."""
    print("🎭 Testing Different Post Types for Meme Descriptions")
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
    
    # Test different subreddits
    subreddits_to_test = ['news', 'cringe', 'pics', 'mildlyinteresting', 'facepalm']
    
    for subreddit_name in subreddits_to_test:
        print(f"\n🔍 Testing r/{subreddit_name}...")
        
        try:
            subreddit = reddit.subreddit(subreddit_name)
            posts = subreddit.hot(limit=3)
            
            for i, post in enumerate(posts):
                if i >= 2:  # Test max 2 posts per subreddit
                    break
                    
                print(f"\n📝 Post {i+1}: {post.title[:60]}...")
                print(f"   Score: {post.score}")
                
                # Generate description
                description = generate_meme_description(
                    post.title,
                    subreddit_name,
                    post.score,
                    post.url if hasattr(post, 'url') else None
                )
                
                print(f"💬 {description}")
                
        except Exception as e:
            print(f"❌ Failed to test r/{subreddit_name}: {e}")
    
    print("\n🎉 Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_different_posts()
