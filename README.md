# VisumateBot

VisumateBot creates stunning videos directly in Telegram. Perfect for quick, creative content! 🎬

## Features
- 📹 Generate **landscape videos** with simple commands.
- 📱 Generate **portrait videos** with simple commands.

## How to Use
1. Start the bot by sending `/start`.
2. Use `/landscapevideo [topic]` to create a landscape video.
3. Use `/portraitvideo [topic]` to create a portrait video.

## Installation (For Developers)
1. Clone the repo:
   ```bash
   git clone https://github.com/vprayag2005/VisumateBot
   cd VisumateBot
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file inside the project directory and add the following:
   ```env
   TELEGRAM_API_KEY = "your_telegram_api_key_here"  # Get from BotFather on Telegram
   GEMINI_API_KEY = "your_gemini_api_key_here"      # Obtain from Gemini API provider
   UNSPLASH_API_KEY = "your_unsplash_api_key_here"  # Get from Unsplash Developers
   BOT_USERNAME = "your_bot_username_here"          # Your bot's username on Telegram
   ```
   Visit the respective websites to obtain the necessary API keys.
5. Run the bot:
   ```bash
   python main.py
   ```

---
🚀 **VisumateBot - Effortless Video Creation!**

