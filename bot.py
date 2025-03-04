import os
import re
import json
import requests
from pyrogram import Client, filters
from flask import Flask
from threading import Thread
from pyrogram.types import (
    InlineQueryResultArticle, 
    InputTextMessageContent, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

# Environment Variables (for Render deployment)
API_ID = os.environ.get('API_ID', '28717442')
API_HASH = os.environ.get('API_HASH', '6be9f19399d55095cfcf08c2e2c2d58c')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7669928411:AAEDBLcyGr8c2Y7iwnraGeSv8OrcV67xwIk')
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'InlinePasteBot')

# Headers for Pastebin request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36",
    "content-type": "application/json",
}

# Pastebin function (unchanged from previous code)
async def p_paste(message, extension=None):
    siteurl = "https://pasty.lus.pm/api/v1/pastes"
    data = {"content": message}
    try:
        response = requests.post(url=siteurl, data=json.dumps(data), headers=HEADERS)
    except Exception as e:
        return {"error": str(e)}
    
    if response.ok:
        response = response.json()
        purl = (
            f"https://pasty.lus.pm/{response['id']}.{extension}"
            if extension
            else f"https://pasty.lus.pm/{response['id']}.txt"
        )
        return {
            "url": purl,
            "raw": f"https://pasty.lus.pm/{response['id']}/raw",
            "bin": "Pasty",
        }
    return {"error": "UNABLE TO REACH pasty.lus.pm"}

# Initialize the bot
app = Client(
    "pastebin_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Start Handler with Inline Buttons
@app.on_message(filters.command(["start"]))
async def start_command(client, message):
    # Create inline keyboard with two buttons
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Paste Text", callback_data="paste_help"),
            InlineKeyboardButton("About Bot", callback_data="about_bot")
        ]
    ])
    
    # Welcome message
    welcome_text = (
        f"👋 Welcome to Pasty Telegram Bot!\n\n"
        "I can help you quickly share and store text online. "
        "Choose an option below to get started."
    )
    
    # Send message with inline keyboard
    await message.reply_text(
        welcome_text, 
        reply_markup=keyboard
    )

# Callback Query Handler for Inline Buttons
@app.on_callback_query()
async def handle_callback(client, callback_query):
    if callback_query.data == "paste_help":
        await callback_query.answer("Paste Help")
        await callback_query.message.edit_text(
            "How to use Paste Feature:\n"
            "1. Use /paste command followed by text\n"
            "2. Or reply to a message with /paste\n"
            "3. For long messages in groups, just mention the bot and use inline",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back to Menu", callback_data="back_to_start")
            ]])
        )
    
    elif callback_query.data == "about_bot":
        await callback_query.answer("About Bot")
        await callback_query.message.edit_text(
            "🤖 Pasty Telegram Bot\n\n"
            "Features:\n"
            "• Quick text sharing\n"
            "• Supports manual and auto paste\n"
            "• Works in groups and private chats",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back to Menu", callback_data="back_to_start")
            ]])
        )
    
    elif callback_query.data == "back_to_start":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Paste Text", callback_data="paste_help"),
                InlineKeyboardButton("About Bot", callback_data="about_bot")
            ]
        ])
        
        await callback_query.message.edit_text(
            f"👋 Welcome to PasteBin Telegram Bot!\n\n"
            "I can help you quickly share and store text online. "
            "Choose an option below to get started.",
            reply_markup=keyboard
        )

# Command handler for manual paste
@app.on_message(filters.command(["paste", "tgpaste"]))
async def manual_paste(client, message):
    # Check if text is provided or replied to
    if len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    elif message.reply_to_message:
        text = message.reply_to_message.text
    else:
        await message.reply_text("Please provide text to paste or reply to a message.")
        return

    # Upload to pastebin
    pablo = await message.reply_text("`Processing...`")
    try:
        paste_result = await p_paste(text, "txt")
        
        if "error" in paste_result:
            await pablo.edit(f"Paste failed: {paste_result['error']}")
            return

        pasted = f"**Successfully Pasted**\n\n" \
                 f"**Link:** [Click Here]({paste_result['url']})\n" \
                 f"**Raw Link:** [Click Here]({paste_result['raw']})"
        
        await pablo.edit(pasted, disable_web_page_preview=True)
    except Exception as e:
        await pablo.edit(f"An error occurred: {str(e)}")

# Inline query handler
@app.on_inline_query()
async def inline_paste(client, query):
    if not query.query:
        return
    
    # Handling larger texts for inline paste
    try:
        # Always try to paste the full text
        paste_result = await p_paste(query.query, "txt")
        
        if "error" in paste_result:
            return
        
        # Truncate text for description to keep it short
        preview_text = (query.query[:100] + '...') if len(query.query) > 100 else query.query
        
        results = [
            InlineQueryResultArticle(
                title="Uploaded Text to Pastebin",
                description=preview_text,
                input_message_content=InputTextMessageContent(
                    f"**Pasted Text**\n\n" 
                    f"**Link:** [Click Here]({paste_result['url']})\n"
                    f"**Raw Link:** [Click Here]({paste_result['raw']})"
                )
            )
        ]
        
        await query.answer(results, cache_time=1)
    except Exception as e:
        print(f"Inline paste error: {e}")
        
# Automatic large text handler
@app.on_message(filters.text & filters.group & ~filters.command(["paste", "tgpaste"]))
async def auto_paste_in_group(client, message):
    # Bot's username (replace with your bot's username)
    BOT_USERNAME = 'TeraboxDemo1Bot'
    
    # Check if message mentions the bot and is very long
    if f'@{BOT_USERNAME}' in message.text and len(message.text) > 1000:
        try:
            paste_result = await p_paste(message.text, "txt")
            
            if "error" in paste_result:
                return
            
            await message.reply(
                f"**Large Text Detected**\n\n"
                f"**Link:** [Click Here]({paste_result['url']})\n"
                f"**Raw Link:** [Click Here]({paste_result['raw']})"
            )
        except Exception:
            pass

# Add a simple web server for Render deployment


web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Main execution
if __name__ == "__main__":
    # Start web server in a separate thread
    web_thread = Thread(target=run_web_server)
    web_thread.start()
    
    # Run the Telegram bot
    print("Bot is running...")
    app.run()

# requirements.txt contents:
# pyrogram
# tgcrypto
# requests
# flask
