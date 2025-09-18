"""
Configuration settings for the Meme Material Radar.

This module contains all configurable parameters for monitoring Reddit posts.
Adjust these values to customize the monitoring behavior.
"""

# Subreddit monitoring configuration with dynamic thresholds
SUBREDDITS = {
    'news': {
        'name': 'news',
        'poll_interval': 20,  # seconds
        'initial_threshold': 10,  # upvotes per minute to start tracking
        'followup_threshold': 15,  # upvotes per minute required to trigger action
        'min_age': 2,  # minimum post age in minutes before any trigger
        'display_name': 'r/news'
    },
    'cringe': {
        'name': 'cringe',
        'poll_interval': 20,  # seconds
        'initial_threshold': 5,  # upvotes per minute to start tracking
        'followup_threshold': 10,  # upvotes per minute required to trigger action
        'min_age': 2,  # minimum post age in minutes before any trigger
        'display_name': 'r/cringe'
    }
}

# Post tracking configuration
POST_TRACKING = {
    'max_posts_per_subreddit': 100,  # Maximum posts to track per subreddit
    'min_post_age_minutes': 5,  # Minimum age for posts to be considered
    'max_post_age_hours': 24,  # Maximum age for posts to be tracked
}

# Logging configuration
LOGGING = {
    'log_file': 'logs/rising_posts.log',
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

# Reddit API configuration
REDDIT_API = {
    'rate_limit_delay': 1,  # seconds to wait between API calls
    'max_retries': 3,  # Maximum retries for failed API calls
    'timeout': 30,  # API request timeout in seconds
}

# Image processing configuration
IMAGE_PROCESSING = {
    'download_images': True,  # Whether to download post images
    'max_image_size_mb': 10,  # Maximum image size to download
    'supported_formats': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'images_folder': 'images',
    'summaries_folder': 'summaries'
}

# Meme package configuration
MEME_PACKAGES = {
    'enabled': True,  # Whether to create complete meme packages
    'packages_folder': 'meme_packages',  # Folder for meme packages
    'include_timestamp': True  # Include timestamp in package folder names
}

# AI Summarization configuration
SUMMARIZATION = {
    'enabled': True,  # Whether to generate summaries
    'model': 'gpt-3.5-turbo',  # OpenAI model to use
    'max_tokens': 150,  # Maximum tokens for witty descriptions (2-3 sentences)
    'temperature': 0.8  # Higher creativity for sarcastic, witty content
}
