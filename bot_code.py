import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import requests
import sqlite3
import telegram

TELEGRAM_API_TOKEN = ""
CHATGPT_API_KEY = ""

# Create a bot instance with your API token
bot = telegram.Bot(token=TELEGRAM_API_TOKEN)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    print("Received start command.")
    update.message.reply_text("Welcome! Type your message to ChatGPT, and I'll get you a response.")

def chat_gpt_request(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {CHATGPT_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "max_tokens": 1000,
        "temperature": 0.3
    }
    response = requests.post("https://api.openai.com/v1/engines/text-davinci-003/completions", headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["text"].strip()

def handle_user_message(update: Update, context: CallbackContext):
    try:
        question = update.message.text

        # Check if the request contains "Yershat"
        if "Yershat" in question:
            response = "I love you too!"
        else:
            response = chat_gpt_request(question)

            # Check if response contains code
            if "```" in response:
                # Wrap code response in markdown-style code block
                response = f"```\n{response}\n```"

        # Escape reserved characters in response
        response = telegram.utils.helpers.escape_markdown(response, version=2)

        # Send the response to the user
        bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode=telegram.ParseMode.MARKDOWN_V2)

    except Exception as e:
        logger.exception(f"An error occurred while handling user message: {str(e)}")
        bot.send_message(chat_id=update.effective_chat.id, text="An error occurred. Please try again later.")


def get_chatgpt_response(update: Update, context: CallbackContext):
    question = update.message.text
    response = chat_gpt_request(question)

    # Check if response contains code
    if "```" in response:
        # Wrap code response in markdown-style code block
        response = f"```\n{response}\n```"

    # Escape reserved characters in response
    response = telegram.utils.helpers.escape_markdown(response, version=2)

    # Send the response to the user
    bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode=telegram.ParseMode.MARKDOWN_V2)

    return ConversationHandler.END

ASK_QUESTION = range(1)

def check_premium_status(user_id: int) -> bool:
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()
    cursor.execute("SELECT is_premium FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    connection.close()

    if user is not None:
        return user[0] == 1
    return False

def ask(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    is_premium = check_premium_status(user_id)
    if is_premium:
        update.message.reply_text("Please enter your question for ChatGPT:")
        return ASK_QUESTION
    else:
        update.message.reply_text("You must be a premium user to access this feature")
        return ConversationHandler.END
    

ask_handler = ConversationHandler(
    entry_points=[CommandHandler("ask", ask)],
    states={
        ASK_QUESTION: [MessageHandler(Filters.text, get_chatgpt_response)],
    },
    fallbacks=[],
)

def main():
    logger.info("Starting main function...")
    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle_user_message))
    dp.add_handler(ask_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()




