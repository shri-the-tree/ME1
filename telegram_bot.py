import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from config import GEMINI_API_KEY, MODEL_NAME, TELEGRAM_TOKEN
from prompt_engineering import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# Dictionary to store conversation history for each user
user_conversations = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! I'm the Marine Edge Assistant. I can help you with questions about IMUCET, "
        "DNS sponsorship, and Marine Edge courses. How can I assist you today?"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "You can ask me about:\n"
        "- IMUCET exam details and dates\n"
        "- Eligibility criteria for marine courses\n"
        "- Marine Edge course offerings\n"
        "- Preparation strategies\n"
        "- DNS sponsorship information\n\n"
        "Just type your question and I'll do my best to help!"
    )


async def get_bot_response(user_id: int, user_input: str) -> str:
    """Get response from the bot using Gemini API."""
    try:
        # Get or initialize conversation history for this user
        if user_id not in user_conversations:
            user_conversations[user_id] = []

        # Create the prompt with system instructions and conversation history
        prompt = SYSTEM_PROMPT + "\n\n"

        # Add conversation history (last few exchanges)
        history = user_conversations[user_id][-10:] if len(user_conversations[user_id]) > 0 else []
        for i, message in enumerate(history):
            if i % 2 == 0:  # Even indices are user messages
                prompt += f"User: {message}\n"
            else:  # Odd indices are bot responses
                prompt += f"Assistant: {message}\n"

        # Add the current user query
        prompt += f"User: {user_input}\nAssistant:"

        # Generate response
        response = model.generate_content(prompt)

        # Extract the text response
        bot_response = response.text

        # Add to history
        user_conversations[user_id].append(user_input)
        user_conversations[user_id].append(bot_response)

        return bot_response

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "I'm sorry, I encountered an error processing your request. Please try again or rephrase your question."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages."""
    user_id = update.effective_user.id
    user_input = update.message.text

    # Show typing indicator while generating response
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # Get response from the bot
    response = await get_bot_response(user_id, user_input)

    # Send the response
    await update.message.reply_text(response)


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot started")


if __name__ == "__main__":
    main()