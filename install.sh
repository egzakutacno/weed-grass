#!/bin/bash
# One-liner installation script for Reddit Meme Material Radar on Ubuntu VPS
# Usage: curl -sSL https://raw.githubusercontent.com/egzakutacno/weed-grass/master/install.sh | bash

set -e  # Exit on any error

echo "🚀 Installing Reddit Meme Material Radar..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip if not already installed
echo "🐍 Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip python3-venv git

# Install system dependencies for image processing
echo "🖼️ Installing image processing dependencies..."
sudo apt install -y libjpeg-dev zlib1g-dev libpng-dev libfreetype6-dev

# Clone the repository
echo "📥 Cloning repository..."
if [ -d "weed-grass" ]; then
    echo "Repository already exists, updating..."
    cd weed-grass
    git pull
else
    git clone https://github.com/egzakutacno/weed-grass.git
    cd weed-grass
fi

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file from template
echo "⚙️ Setting up configuration..."
if [ ! -f "config/.env" ]; then
    cp config/env_template.txt config/.env
    echo "📝 Created config/.env from template"
    echo "⚠️  Please edit config/.env and add your Reddit API credentials!"
else
    echo "✅ config/.env already exists"
fi

# Create logs directory
mkdir -p logs

# Make the main script executable
chmod +x src/meme_radar.py

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit config/.env with your Reddit API credentials:"
echo "   nano config/.env"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the bot:"
echo "   python src/meme_radar.py"
echo ""
echo "4. To run in background (with screen):"
echo "   screen -S reddit-bot"
echo "   source venv/bin/activate"
echo "   python src/meme_radar.py"
echo "   # Press Ctrl+A then D to detach"
echo ""
echo "5. To reattach to background session:"
echo "   screen -r reddit-bot"
echo ""
echo "🎉 Happy meme hunting!"
