# Telegram Image to Link Bot

## Overview

Telegram bot ដែលទទួលរូបភាព ហើយ upload ទៅ ImgBB ឬ Litterbox ដើម្បីបង្ហូរ link ជាមួយ preview។ Bot គាំទ្រ webhook mode សម្រាប់ deploy នៅលើ Vercel។

## Stack

- **Language**: Python 3.12
- **Bot Framework**: python-telegram-bot >= 22.7
- **HTTP Client**: httpx >= 0.27.0
- **Image Hosting**: ImgBB (permanent) / Litterbox (72h fallback)
- **Deployment**: Vercel (webhook) / local (polling)

## Project Structure

```
bot.py              # Core bot logic + handlers (importable)
api/
  webhook.py        # Vercel serverless — POST /api/webhook (Telegram)
  ping.py           # Vercel serverless — HEAD/GET /api/ping (UptimeRobot)
vercel.json         # Vercel runtime config (python3.12)
requirements.txt    # Python dependencies for Vercel
pyproject.toml      # Local dev dependencies (uv)
```

## Features

- `/start` — ស្វាគមន៍ user និងណែនាំ
- Photo message → upload → return public link
- Document (image) message → upload → return public link
- Unknown message → redirect user to send photo

## Environment Variables

- `TELEGRAM_BOT_TOKEN` — Bot token ពី @BotFather (required)
- `IMGBB_API_KEY` — ImgBB API key សម្រាប់ permanent links (optional)

## Deploy on Vercel

1. Push code ទៅ GitHub
2. Import project ចូល Vercel
3. Add environment variables: `TELEGRAM_BOT_TOKEN`, `IMGBB_API_KEY`
4. Deploy — Vercel domain នឹងជា `https://<your-domain>`
5. Set webhook:
   ```
   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-domain>/api/webhook
   ```

## UptimeRobot Ping

- URL: `https://<your-domain>/api/ping`
- Monitor type: **HTTP(s)** with **HEAD** request
- Expected status: `200 OK`

## Local Development (Polling)

```bash
python3 bot.py
```
