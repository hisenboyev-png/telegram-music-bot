# Telegram Bot 24/7 Hosting Guide

## 📋 Prerequisites
- Your bot token: `8593214580:AAFMX9dy_83cUv0QGur1OyvwHqCwM6kbS5c`
- All files in this directory (especially bot.py, requirements.txt, Procfile, runtime.txt)
- FFmpeg files (already extracted)

## 🚀 Free Hosting Options

### Option 1: Heroku (Recommended)
1. **Create Heroku Account**: https://heroku.com
2. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli
3. **Deploy Steps**:
   ```bash
   # Login to Heroku
   heroku login
   
   # Create new app
   heroku create your-bot-name
   
   # Set environment variable
   heroku config:set BOT_TOKEN=8593214580:AAFMX9dy_83cUv0QGur1OyvwHqCwM6kbS5c
   
   # Deploy
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

### Option 2: Railway
1. **Create Railway Account**: https://railway.app
2. **Connect GitHub repository** or upload files directly
3. **Deploy automatically** (Railway detects Procfile)

### Option 3: Render
1. **Create Render Account**: https://render.com
2. **Create Web Service** (but use worker process)
3. **Upload files** and deploy

## 🔧 Configuration Files

### Procfile
```
worker: python bot.py
```

### requirements.txt
```
python-telegram-bot
requests
yt-dlp
```

### runtime.txt
```
python-3.10.0
```

## 📁 File Structure
```
├── bot.py                    # Main bot code
├── requirements.txt          # Python dependencies
├── Procfile                 # Heroku process definition
├── runtime.txt              # Python version
├── ffmpeg-master-latest-win64-gpl/  # FFmpeg tools
│   └── bin/
│       ├── ffmpeg.exe
│       └── ffprobe.exe
└── deploy.sh                # Deployment script
```

## ⚠️ Important Notes

1. **Worker Process**: This bot runs as a worker process, not a web server
2. **FFmpeg**: Already included and configured in bot.py
3. **Environment Variables**: Store your BOT_TOKEN securely
4. **Free Tier Limits**: Be aware of free tier limitations on hosting platforms

## 🔍 Monitoring

After deployment, you can check logs using:
```bash
# Heroku logs
heroku logs --tail

# Railway logs
railway logs
```

## 🆘 Troubleshooting

If bot stops working:
1. Check logs for errors
2. Verify BOT_TOKEN is set correctly
3. Ensure all files are deployed
4. Check if hosting platform has any issues

## 🔄 Auto-restart

Most platforms automatically restart your bot if it crashes. For additional reliability, consider adding error handling in your bot code.