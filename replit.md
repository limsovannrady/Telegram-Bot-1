# Telegram Image to Link Bot

## Overview

Telegram bot ដែលទទួលរូបភាព ហើយ upload ទៅ Telegraph (telegra.ph) ដើម្បីបង្ហូរ link ជាមួយ preview។

## Stack

- **Language**: Python 3.11
- **Bot Framework**: python-telegram-bot >= 22.7
- **HTTP Client**: httpx >= 0.27.0
- **Image Hosting**: Telegraph (telegra.ph/upload)

## Features

- `/start` — ស្វាគមន៍ user និងណែនាំ
- `/help` — បង្ហាញការណែនាំការប្រើប្រាស់
- Photo message → upload to Telegraph → return link with preview
- Document (image) message → upload to Telegraph → return link with preview
- Unknown message → redirect user to send photo

## How it works

1. User ផ្ញើ Photo ឬ Image file
2. Bot download file ពី Telegram servers
3. Bot upload ទៅ `https://telegra.ph/upload`
4. Telegraph ត្រឡប់ path `/file/xxx.jpg`
5. Bot ផ្ញើ `https://telegra.ph/file/xxx.jpg` link មកវិញ
6. Link នោះ auto-preview នៅក្នុង Telegram chats

## Environment Variables

- `TELEGRAM_BOT_TOKEN` — Bot token ពី @BotFather

## Running

```bash
python3 bot.py
```
