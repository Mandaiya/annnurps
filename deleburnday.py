import os
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from pymongo import MongoClient
from datetime import datetime, timedelta
import threading

# Environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_DB_URI")

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client["birthday_bot"]
users_collection = db["users"]

# Register birthday
def register_birthday(update: Update, context: CallbackContext):
    user = update.effective_user
    if len(context.args) != 1:
        update.message.reply_text("Please provide your birthday in the format: YYYY-MM-DD\nExample: /register_birthday 1995-07-14")
        return

    try:
        birthday = datetime.strptime(context.args[0], "%Y-%m-%d").date()
    except ValueError:
        update.message.reply_text("Invalid date format. Please use YYYY-MM-DD.")
        return

    user_data = {
        "user_id": user.id,
        "username": user.username or f"User_{user.id}",
        "birthday": birthday.isoformat()
    }

    users_collection.update_one(
        {"user_id": user.id},
        {"$set": user_data},
        upsert=True
    )

    update.message.reply_text(f"Your birthday has been registered as {birthday}. 🎉")

# Notify users about upcoming birthdays
def notify_users():
    bot = Bot(BOT_TOKEN)

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    # Find users with birthdays tomorrow
    birthdays_tomorrow = list(users_collection.find({"birthday": tomorrow.isoformat()}))

    if birthdays_tomorrow:
        all_users = list(users_collection.find())
        birthday_users = ", ".join([f"@{user['username']}" for user in birthdays_tomorrow])

        for user in all_users:
            bot.send_message(
                chat_id=user["user_id"],
                text=f"🎉 Reminder: Tomorrow is the birthday of {birthday_users}! Don't forget to wish them!"
            )

# Birthday Wishing System
def send_wishes():
    bot = Bot(BOT_TOKEN)

    today = datetime.now().date()

    # Find users with birthdays today
    birthdays_today = list(users_collection.find({"birthday": today.isoformat()}))

    if birthdays_today:
        all_users = list(users_collection.find())
        for user in all_users:
            for birthday_user in birthdays_today:
                bot.send_message(
                    chat_id=user["user_id"],
                    text=f"🎉 Today is @{birthday_user['username']}'s birthday! Send them your wishes! 🎂"
                )

# Schedule daily reminders
def start_schedulers():
    def daily_tasks():
        while True:
            now = datetime.now()
            next_run = (datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1))
            sleep_duration = (next_run - now).total_seconds()

            # Sleep until midnight
            threading.Timer(sleep_duration, notify_users).start()
            threading.Timer(sleep_duration, send_wishes).start()

    thread = threading.Thread(target=daily_tasks, daemon=True)
    thread.start()

# Main function
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("register_birthday", register_birthday))

    # Start the bot
    updater.start_polling()
    updater.idle()

    # Start schedulers
    start_schedulers()

if __name__ == "__main__":
    main()
