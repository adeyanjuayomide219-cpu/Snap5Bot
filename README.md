# Snap5Bot 🤖

A multipurpose Telegram bot with:
- 🖼️ Image Converter (PNG, JPG, WEBP, BMP)
- 🎨 AI Image Generator (via HuggingFace)
- 🔗 URL Shortener (via TinyURL)

## Deployment

1. Fork this repository
2. Deploy on Railway
3. Add `TELEGRAM_TOKEN` environment variable
4. (Optional) Add `HUGGINGFACE_API_KEY` for image generation

## Commands

- `/start` - Show main menu
- `/help` - Show help
- `/generate [prompt]` - Generate image
- `/shorten [url]` - Shorten URL
- `/cancel` - Cancel current operation

## Environment Variables

- `TELEGRAM_TOKEN` - Your bot token from @BotFather
- `HUGGINGFACE_API_KEY` - (Optional) For AI image generation

## License

MIT
