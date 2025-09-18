#!/bin/bash

# Reddit Meme Radar Bot - Linux VPS Installation Script
# Completely uninterrupted installation for Ubuntu/Debian systems

set -e  # Exit on any error

echo "🚀 Starting Reddit Meme Radar Bot installation..."

# Update package lists and upgrade system (completely non-interactive)
export DEBIAN_FRONTEND=noninteractive
export UCF_FORCE_CONFFNEW=1

echo "📦 Updating system packages..."
apt-get update -y
apt-get upgrade -y -o Dpkg::Options::="--force-confnew" -o Dpkg::Options::="--force-confdef"
apt-get autoremove -y
apt-get autoclean -y

# Install essential packages
echo "🔧 Installing essential packages..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    screen \
    htop \
    nano \
    vim

# Clean up environment variables
unset DEBIAN_FRONTEND
unset UCF_FORCE_CONFFNEW

# Clone the repository
echo "📥 Cloning repository..."
if [ -d "weed-grass" ]; then
    echo "⚠️  Directory 'weed-grass' already exists. Removing it..."
    rm -rf weed-grass
fi

git clone https://github.com/egzakutacno/weed-grass.git
cd weed-grass

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p images
mkdir -p meme_packages
mkdir -p logs
mkdir -p summaries

# Set proper permissions
echo "🔐 Setting permissions..."
chmod +x src/meme_radar.py
chmod 755 images meme_packages logs summaries

# Create .env file from template
echo "⚙️  Setting up configuration..."
if [ ! -f "config/.env" ]; then
    cp config/env.example config/.env
    echo "📝 Created .env file from template. Please edit config/.env with your API credentials."
else
    echo "✅ .env file already exists."
fi

# Create systemd service file for easy management
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/reddit-meme-bot.service << EOF
[Unit]
Description=Reddit Meme Radar Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python src/meme_radar.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable reddit-meme-bot.service

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit your Reddit API credentials:"
echo "   nano config/.env"
echo ""
echo "2. Start the bot:"
echo "   systemctl start reddit-meme-bot"
echo ""
echo "3. Check bot status:"
echo "   systemctl status reddit-meme-bot"
echo ""
echo "4. View logs:"
echo "   journalctl -u reddit-meme-bot -f"
echo ""
echo "5. Stop the bot:"
echo "   systemctl stop reddit-meme-bot"
echo ""
echo "6. Alternative: Run manually in screen:"
echo "   screen -S reddit-bot"
echo "   source venv/bin/activate"
echo "   python src/meme_radar.py"
echo "   # Press Ctrl+A then D to detach"
echo ""
echo "7. Reattach to screen session:"
echo "   screen -r reddit-bot"
echo ""
echo "🎉 Your Reddit Meme Radar Bot is ready to go!"
