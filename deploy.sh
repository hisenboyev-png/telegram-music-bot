#!/bin/bash
# Deployment script for Telegram Bot

echo "Starting Telegram Bot deployment..."

# Install dependencies
pip install -r requirements.txt

# Make sure ffmpeg is available
if [ ! -f "ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe" ]; then
    echo "FFmpeg not found, extracting..."
    unzip -q ffmpeg.zip
fi

echo "Bot is ready to run!"
echo "To start the bot, run: python bot.py"
echo "For 24/7 hosting, deploy to Heroku, Railway, or similar platform"