import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    Filters
)
import pickle
import os
from threading import Timer
import calendar

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

# Global variables
BIRTHDAY_FILE = 'birthdays.pkl'
ADMIN_ID = None  # Set your Telegram user ID here

def load_birthdays():
    if os.path.exists(BIRTHDAY_FILE):
        with open(BIRTHDAY_FILE, 'rb') as f:
            return pickle.load(f)
    return {}

def save_birthdays(birthdays):
    with open(BIRTHDAY_FILE, 'wb') as f:
        pickle.dump(birthdays, f)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "🎉 Welcome to the Birthday Calendar Bot! 🎉\n\n"
        "Use /addbirthday to add your birthday\n"
        "Use /mybirthday to check your stored birthday\n"
        "Admins can use /birthdaysthismonth to see this month's birthdays"
    )

def add_birthday(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    args = context.args
    
    if not args or len(args) != 2:
        update.message.reply_text(
            "Please enter your birthday in format: /addbirthday DD MM\n"
            "Example: /addbirthday 15 04 for April 15th"
        )
        return
    
    try:
        day = int(args[0])
        month = int(args[1])
        
        if month < 1 or month > 12:
            raise ValueError("Invalid month")
        
        max_day = calendar.monthrange(2020, month)[1]
        if day < 1 or day > max_day:
            raise ValueError(f"Invalid day for month {month}")
        
        birthdays = load_birthdays()
        birthdays[user.id] = {
            'day': day,
            'month': month,
            'name': user.full_name,
            'username': user.username
        }
        save_birthdays(birthdays)
        
        update.message.reply_text(
            f"🎂 Birthday saved! We'll remember you on {day}/{month}"
        )
    except ValueError as e:
        update.message.reply_text(f"Invalid date: {e}\nPlease use format: /addbirthday DD MM")

def my_birthday(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    birthdays = load_birthdays()
    
    if user.id in birthdays:
        bday = birthdays[user.id]
        update.message.reply_text(
            f"Your birthday is stored as: {bday['day']}/{bday['month']}"
        )
    else:
        update.message.reply_text(
            "You haven't added your birthday yet. Use /addbirthday DD MM"
        )

def birthdays_this_month(update: Update, context: CallbackContext) -> None:
    if ADMIN_ID and update.effective_user.id != ADMIN_ID:
        update.message.reply_text("Sorry, this command is only for admins.")
        return
    
    current_month = datetime.now().month
    birthdays = load_birthdays()
    
    month_birthdays = [
        (bday['day'], bday['name'], bday.get('username', '')) 
        for user_id, bday in birthdays.items() 
        if bday['month'] == current_month
    ]
    
    if not month_birthdays:
        update.message.reply_text("No birthdays this month!")
        return
    
    month_birthdays.sort()
    
    response = "🎉 Birthdays this month:\n\n"
    for day, name, username in month_birthdays:
        response += f"{day}/{current_month}: {name}"
        if username:
            response += f" (@{username})"
        response += "\n"
    
    update.message.reply_text(response)

def send_monthly_report(context: CallbackContext):
    if not ADMIN_ID:
        return
    
    current_month = datetime.now().month

month_name = datetime.now().strftime('%B')
    birthdays = load_birthdays()
    
    month_birthdays = [
        (bday['day'], bday['name'], bday.get('username', '')) 
        for user_id, bday in birthdays.items() 
        if bday['month'] == current_month
    ]
    
    if not month_birthdays:
        message = f"No birthdays in {month_name}!"
    else:
        month_birthdays.sort()
        message = f"🎉 Birthdays in {month_name}:\n\n"
        for day, name, username in month_birthdays:
            message += f"{day}/{current_month}: {name}"
            if username:
                message += f" (@{username})"
            message += "\n"
    
    context.bot.send_message(chat_id=ADMIN_ID, text=message)

def schedule_monthly_report(updater):
    now = datetime.now()
    next_month = now.month % 12 + 1
    next_year = now.year + (1 if next_month == 1 else 0)
    next_report = datetime(next_year, next_month, 1, 9, 0)
    delay = (next_report - now).total_seconds()
    Timer(delay, lambda: send_monthly_report(updater.dispatcher) and schedule_monthly_report(updater)).start()

def main() -> None:
    TOKEN = "7621821845:AAGGPOS6VpwXLDGsYvMaANaEAEVFTy3qYpg"
    global ADMIN_ID
    ADMIN_ID = 655594746  # Replace with your Telegram user ID
    
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("addbirthday", add_birthday))
    dispatcher.add_handler(CommandHandler("mybirthday", my_birthday))
    dispatcher.add_handler(CommandHandler("birthdaysthismonth", birthdays_this_month))
    
    # Handle all text messages that aren't commands
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, start))
    
    updater.start_polling()
    schedule_monthly_report(updater)
    updater.idle()

if __name__ == '__main__':
    main()
