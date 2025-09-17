# Meme Material Radar

A Python tool that monitors Reddit for fast-rising posts in r/news and r/cringe, helping you spot viral content as it gains traction.

## Features

- **Dynamic Threshold System**: Uses initial and follow-up thresholds to avoid false positives
- **Real-time Monitoring**: Tracks posts with configurable polling intervals
- **Smart Detection**: Only flags posts with sustained momentum, not early spikes
- **Snapshot Tracking**: Maintains post history for accurate rate calculations
- **Moving Averages**: Smooths out noise to detect genuine trends
- **Comprehensive Logging**: Logs rising posts with detailed metrics
- **Memory Management**: Automatically cleans up old posts to prevent memory issues
- **Configurable**: Easy to adjust thresholds, polling intervals, and other settings

## Quick Installation (Ubuntu VPS)

**One-liner installation:**
```bash
curl -sSL https://raw.githubusercontent.com/egzakutacno/weed-grass/master/install.sh | bash
```

**Manual installation:**
```bash
# Clone repository
git clone https://github.com/egzakutacno/weed-grass.git
cd weed-grass

# Install dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
pip3 install -r requirements.txt

# Setup configuration
cp config/env_template.txt config/.env
# Edit config/.env with your Reddit API credentials
```

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
├── install.sh                 # One-liner installation script
└── README.md                  # This file
```

## Prerequisites

- Python 3.7 or higher
- Reddit account
- Reddit API credentials (see setup instructions below)

## Installation

1. **Clone or download this project**
   ```bash
   git clone https://github.com/egzakutacno/weed-grass.git
   cd weed-grass
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
2024-01-15 10:32:45 - INFO - Started tracking post abc123 with initial rate 12.5 upvotes/min
2024-01-15 10:33:15 - INFO - RISING POST DETECTED in r/news!
  Title: Breaking: Major news story here
  URL: https://reddit.com/r/news/comments/abc123/
  Current Score: 1250
  Upvote Rate: 18.3 upvotes/min
  Moving Avg Rate: 16.7 upvotes/min
  Comment Rate: 25.3 comments/min
  Initial Rate: 12.5 upvotes/min
  Follow-up Threshold: 15 upvotes/min
  Snapshots: 4
  ==================================================
```

### Running on VPS (Background)

To run the bot in the background on a VPS:

```bash
# Using screen (recommended)
screen -S reddit-bot
python src/meme_radar.py
# Press Ctrl+A then D to detach

# To reattach later
screen -r reddit-bot

# Using nohup
nohup python src/meme_radar.py > bot.log 2>&1 &
```

### Stopping the Tool

Press `Ctrl+C` to gracefully stop the monitoring tool.

## Configuration

### Dynamic Threshold System

The bot uses a sophisticated two-stage threshold system:

1. **Initial Threshold**: Post must meet this rate to start tracking
2. **Follow-up Threshold**: Post must meet this rate to trigger action
3. **Minimum Age**: Post must be at least this old before any checks

Edit `config/settings.py` to customize monitoring behavior:

```python
SUBREDDITS = {
    'news': {
        'name': 'news',
        'poll_interval': 20,  # Check every 20 seconds
        'initial_threshold': 10,  # Start tracking if > 10 upvotes/min
        'followup_threshold': 15,  # Trigger if > 15 upvotes/min
        'min_age': 2,  # Minimum post age in minutes
        'display_name': 'r/news'
    },
    'cringe': {
        'name': 'cringe',
        'poll_interval': 20,  # Check every 20 seconds
        'initial_threshold': 5,  # Start tracking if > 5 upvotes/min
        'followup_threshold': 10,  # Trigger if > 10 upvotes/min
        'min_age': 2,  # Minimum post age in minutes
        'display_name': 'r/cringe'
    }
}
```

### Other Settings

- **POST_TRACKING**: Control how many posts to track and their age limits
- **LOGGING**: Configure log levels and output format
- **REDDIT_API**: Adjust API rate limiting and retry behavior

## How the Dynamic Threshold System Works

1. **Post Discovery**: When a post is found, it's checked for minimum age
2. **Initial Tracking**: If the post meets the initial threshold, tracking begins
3. **Snapshot Collection**: Each poll adds a new snapshot with current metrics
4. **Rate Calculation**: Uses snapshots to calculate true momentum over time
5. **Trigger Decision**: Only triggers when follow-up threshold is exceeded
6. **One-Time Trigger**: Once triggered, post won't trigger again (prevents spam)

### Benefits

- **Reduces False Positives**: Early spikes won't trigger the bot
- **Detects True Momentum**: Only posts with sustained growth are flagged
- **Subreddit-Specific**: Different thresholds for different communities
- **Noise Reduction**: Moving averages smooth out temporary fluctuations
- **Memory Efficient**: Automatic cleanup of old snapshots

## Logging

The tool creates detailed logs in `logs/rising_posts.log` with timestamps and full post details. Logs include:

- Subreddit name
- Post title
- Post URL
- Current score
- Upvote rate (upvotes per minute)
- Moving average rate
- Comment rate (comments per minute)
- Initial rate and thresholds
- Number of snapshots
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
        'initial_threshold': 8,
        'followup_threshold': 12,
        'min_age': 3,
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
   - Verify your Reddit credentials are correct
   - Check your internet connection
   - Ensure Reddit API is accessible

3. **High memory usage**
   - The bot automatically cleans up old posts
   - Adjust `max_posts_per_subreddit` in settings if needed

4. **Too many false positives**
   - Increase the `followup_threshold` values
   - Increase the `min_age` to wait longer before checking

5. **Missing posts**
   - Decrease the `initial_threshold` values
   - Check if posts are being blacklisted

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.