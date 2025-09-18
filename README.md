# Reddit Meme Radar Bot

A Python bot that monitors Reddit for trending posts and generates meme descriptions using AI.

## Features

- Monitors multiple subreddits (r/news, r/cringe)
- Dynamic threshold system to detect "hot" posts
- Downloads images from posts
- Generates AI-powered meme descriptions (9gag/Reddit trolling style)
- Creates organized meme packages with metadata
- Prevents duplicate processing
- Linux VPS ready with systemd service

## Quick Start (Linux VPS)

### One-Liner Installation:
```bash
curl -sSL https://raw.githubusercontent.com/egzakutacno/weed-grass/master/install-linux.sh | bash
```

This will:
- Install all dependencies (completely non-interactive)
- Set up Python virtual environment
- Create systemd service for easy management
- Configure all necessary directories

### After Installation:

1. **Edit your API credentials:**
```bash
nano config/.env
```

2. **Start the bot:**
```bash
systemctl start reddit-meme-bot
```

3. **Check status:**
```bash
systemctl status reddit-meme-bot
```

4. **View logs:**
```bash
journalctl -u reddit-meme-bot -f
```

## Manual Installation

### Prerequisites
- Python 3.8+
- Reddit API credentials
- OpenAI API key (optional, for descriptions)

### Setup
```bash
git clone https://github.com/egzakutacno/weed-grass.git
cd weed-grass
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config/env.example config/.env
# Edit config/.env with your API credentials
python src/meme_radar.py
```

## Configuration

Edit `config/settings.py` to customize:
- Subreddits to monitor
- Dynamic threshold settings (initialThreshold, followupThreshold, minAge)
- Polling intervals
- AI model settings

## Bot Management

### Using Systemd (Production):
```bash
# Start
systemctl start reddit-meme-bot

# Stop
systemctl stop reddit-meme-bot

# Restart
systemctl restart reddit-meme-bot

# Enable auto-start on boot
systemctl enable reddit-meme-bot

# View logs
journalctl -u reddit-meme-bot -f
```

### Using Screen (Testing):
```bash
# Start screen session
screen -S reddit-bot
source venv/bin/activate
python src/meme_radar.py
# Press Ctrl+A then D to detach

# Reattach
screen -r reddit-bot
```

## Features

### Dynamic Threshold System
- **initialThreshold**: upvotes/minute to start tracking
- **followupThreshold**: upvotes/minute required to trigger action
- **minAge**: minimum post age before any trigger
- Prevents false positives from early spikes
- Only triggers posts genuinely "picking up momentum"

### AI Description Style
- 9gag/Reddit trolling style
- 1-2 sentences maximum
- Mocking and trolling instead of explaining
- Examples: "peak nfl cringe", "bro really brought his waifu to prom"

### Meme Package Creation
- Creates individual folders for every downloaded image
- Human-readable folder names
- Complete metadata (JSON, AI description, URLs, README)
- Prevents duplicate posts

## Troubleshooting

### Common Issues:

1. **Installation fails**: Make sure you have root access and internet connection
2. **ModuleNotFoundError**: Activate virtual environment (`source venv/bin/activate`)
3. **API errors**: Check your credentials in `config/.env`
4. **Permission errors**: Run with `sudo` or check file permissions

### Logs:
- Bot activity: `logs/rising_posts.log`
- System logs: `journalctl -u reddit-meme-bot -f`
- Screen logs: `screen -r reddit-bot`

## File Structure

```
weed-grass/
├── src/
│   └── meme_radar.py          # Main bot script
├── config/
│   ├── settings.py            # Configuration
│   ├── env.example            # Environment template
│   └── .env                   # Your API credentials (not in git)
├── images/                    # Downloaded images (not in git)
├── meme_packages/             # Generated meme packages (not in git)
├── logs/                      # Bot logs (not in git)
├── install-linux.sh           # Linux installation script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## License

MIT License - feel free to use and modify!