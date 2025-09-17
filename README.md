# Meme Material Radar

A Python tool that monitors Reddit for fast-rising posts in r/news and r/cringe, helping you spot viral content as it gains traction.

## Features

- **Real-time Monitoring**: Tracks posts in r/news and r/cringe with configurable polling intervals
- **Smart Thresholds**: Flags posts that exceed upvote rate thresholds (100/min for news, 50/min for cringe)
- **Comprehensive Logging**: Logs rising posts with detailed metrics to both console and file
- **Memory Management**: Automatically cleans up old posts to prevent memory issues
- **Configurable**: Easy to adjust thresholds, polling intervals, and other settings

## Project Structure

```
meme-material-radar/
├── src/
│   └── meme_radar.py          # Main monitoring script
├── config/
│   ├── settings.py            # Configuration settings
│   └── env_template.txt       # Environment variables template
├── logs/
│   └── rising_posts.log       # Log file for rising posts (created automatically)
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Prerequisites

- Python 3.7 or higher
- Reddit account
- Reddit API credentials (see setup instructions below)

## Installation

1. **Clone or download this project**
   ```bash
   git clone <repository-url>
   cd meme-material-radar
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Reddit API credentials**
   
   a. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
   
   b. Click "Create App" or "Create Another App"
   
   c. Fill in the form:
      - **Name**: `meme-material-radar` (or any name you prefer)
      - **App type**: Select "script"
      - **Description**: `Reddit post monitoring tool`
      - **About URL**: Leave blank
      - **Redirect URI**: `http://localhost:8080` (required but not used)
   
   d. Click "Create app"
   
   e. Note down your **Client ID** (under the app name) and **Client Secret**

4. **Configure environment variables**
   
   a. Copy the template file:
      ```bash
   cp config/env_template.txt config/.env
   ```
   
   b. Edit `config/.env` and fill in your Reddit credentials:
      ```
      REDDIT_CLIENT_ID=your_actual_client_id_here
      REDDIT_CLIENT_SECRET=your_actual_client_secret_here
      REDDIT_USERNAME=your_reddit_username
      REDDIT_PASSWORD=your_reddit_password
      REDDIT_USER_AGENT=meme-material-radar/1.0 (by /u/your_username)
      ```

## Usage

### Basic Usage

Run the monitoring tool:

```bash
python src/meme_radar.py
```

The tool will start monitoring both subreddits and display output like:

```
Meme Material Radar - Reddit Post Monitoring Tool
==================================================
2024-01-15 10:30:15 - INFO - Successfully connected to Reddit API
2024-01-15 10:30:15 - INFO - Starting Meme Material Radar...
2024-01-15 10:30:15 - INFO - Starting monitoring for r/news
2024-01-15 10:30:15 - INFO - Starting monitoring for r/cringe
2024-01-15 10:32:45 - INFO - RISING POST DETECTED in r/news!
  Title: Breaking: Major news story here
  URL: https://reddit.com/r/news/comments/abc123/
  Current Score: 1250
  Upvote Rate: 150.5 upvotes/min
  Comment Rate: 25.3 comments/min
  Threshold: 100 upvotes/min
  ==================================================
```

### Stopping the Tool

Press `Ctrl+C` to gracefully stop the monitoring tool.

## Configuration

### Adjusting Thresholds and Intervals

Edit `config/settings.py` to customize monitoring behavior:

```python
SUBREDDITS = {
    'news': {
        'name': 'news',
        'poll_interval': 60,  # Check every 60 seconds
        'upvote_rate_threshold': 100,  # Flag if > 100 upvotes/min
        'display_name': 'r/news'
    },
    'cringe': {
        'name': 'cringe',
        'poll_interval': 120,  # Check every 120 seconds
        'upvote_rate_threshold': 50,  # Flag if > 50 upvotes/min
        'display_name': 'r/cringe'
    }
}
```

### Other Settings

- **POST_TRACKING**: Control how many posts to track and their age limits
- **LOGGING**: Configure log levels and output format
- **REDDIT_API**: Adjust API rate limiting and retry behavior

## Logging

The tool creates detailed logs in `logs/rising_posts.log` with timestamps and full post details. Logs include:

- Subreddit name
- Post title
- Post URL
- Current score
- Upvote rate (upvotes per minute)
- Comment rate (comments per minute)
- Detection timestamp

## Monitoring Different Subreddits

To monitor different subreddits, edit `config/settings.py`:

1. Add new subreddit entries to the `SUBREDDITS` dictionary
2. Adjust polling intervals and thresholds as needed
3. Restart the tool

Example for adding r/technology:

```python
SUBREDDITS = {
    'news': { ... },
    'cringe': { ... },
    'technology': {
        'name': 'technology',
        'poll_interval': 90,
        'upvote_rate_threshold': 75,
        'display_name': 'r/technology'
    }
}
```

## Troubleshooting

### Common Issues

1. **"Missing Reddit API credentials" error**
   - Ensure `config/.env` exists and contains all required variables
   - Check that your Reddit app is set up correctly

2. **"Failed to connect to Reddit API" error**
   - Verify your credentials are correct
   - Check your internet connection
   - Ensure your Reddit account is not suspended

3. **Rate limiting errors**
   - The tool includes built-in rate limiting
   - If you see rate limit errors, increase the `rate_limit_delay` in settings

4. **No posts being detected**
   - Check that the subreddits exist and are accessible
   - Verify your thresholds aren't too high
   - Ensure posts are within the age limits

### Debug Mode

To see more detailed logging, change the log level in `config/settings.py`:

```python
LOGGING = {
    'log_level': 'DEBUG',  # Change from 'INFO' to 'DEBUG'
    # ... other settings
}
```

## Dependencies

- **praw**: Python Reddit API Wrapper for accessing Reddit data
- **python-dotenv**: For loading environment variables from .env files

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## Disclaimer

This tool is for educational and personal use. Please respect Reddit's API terms of service and rate limits. The tool includes built-in rate limiting, but use responsibly.
