Podangu, [05-04-2025 02:52]
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import calendar
from threading import Timer
import sqlite3

# Initialize logging correctly
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)  # Fixed: Correct capitalization and name

# Database setup
def init_db():
    conn = sqlite3.connect('birthdays.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS birthdays
                 (user_id INTEGER PRIMARY KEY,
                  day INTEGER,
                  month INTEGER,
                  name TEXT,
                  username TEXT)''')
    conn.commit()
    conn.close()

def save_birthday(user_id, day, month, name, username):
    conn = sqlite3.connect('birthdays.db')
    c = conn.cursor()
    c.execute("REPLACE INTO birthdays VALUES (?, ?, ?, ?, ?)", 
              (user_id, day, month, name, username))
    conn.commit()
    conn.close()

def load_birthdays():
    conn = sqlite3.connect('birthdays.db')
    c = conn.cursor()
    c.execute("SELECT * FROM birthdays")
    birthdays = {row[0]: {'day': row[1], 'month': row[2], 'name': row[3], 'username': row[4]} 
                for row in c.fetchall()}
    conn.close()
    return birthdays

# Initialize database
init_db()

ADMIN_ID = 655594746  # Set your admin ID here

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "🎉 Welcome to the Birthday Calendar Bot! 🎉\n\n"
        "Use /addbirthday DD MM to add your birthday\n"
        "Use /mybirthday to check your stored birthday\n"
        "Admins: /birthdaysthismonth to see this month's birthdays"
    )

def add_birthday(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    args = context.args
    
    if not args or len(args) != 2:
        update.message.reply_text("Usage: /addbirthday DD MM (e.g., /addbirthday 15 04)")
        return
    
    try:
        day = int(args[0])
        month = int(args[1])
        
        if month < 1 or month > 12:
            raise ValueError("Month must be 1-12")
        
        max_day = calendar.monthrange(2020, month)[1]
        if day < 1 or day > max_day:
            raise ValueError(f"Day must be 1-{max_day} for month {month}")
        
        save_birthday(user.id, day, month, user.full_name, user.username)
        update.message.reply_text(f"🎂 Birthday saved! We'll remember you on {day}/{month}")
    except ValueError as e:
        update.message.reply_text(f"Error: {e}\nUsage: /addbirthday DD MM")

def my_birthday(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    birthdays = load_birthdays()
    
    if user.id in birthdays:
        bday = birthdays[user.id]
        update.message.reply_text(f"Your birthday: {bday['day']}/{bday['month']}")
    else:
        update.message.reply_text("You haven't added your birthday yet. Use /addbirthday DD MM")

def birthdays_this_month(update: Update, context: CallbackContext) -> None:
    if ADMIN_ID and update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Admin only command")
        return
    
    current_month = datetime.now().month
    birthdays = load_birthdays()
    
    month_birthdays = [
        (bday['day'], bday['name'], bday.get('username', '')) 
        for bday in birthdays.values() 
        if bday['month'] == current_month
    ]
    
    if not month_birthdays:
        update.message.reply_text("No birthdays this month!")
        return
    
    month_birthdays.sort()
    response = "🎉 Birthdays this month:\n\n" + "\n".join(
        f"{day}/{current_month}: {name}{' (@' + username + ')' if username else ''}"
        for day, name, username in month_birthdays
    )
    update.message.reply_text(response)

def send_monthly_report(context: CallbackContext):
    if not ADMIN_ID:
        return
    
    current_month = datetime.now().month
    month_name = datetime.now().strftime('%B')
    birthdays = load_birthdays()
    
    month_birthdays = [
        (bday['day'], bday['name'], bday.get('username', '')) 
        for bday in birthdays.values() 
        if bday['month'] == current_month
    ]
    
    if not month_birthdays:
        message = f"No birthdays in {month_name}!"
    else:
        month_birthdays.sort()
        message = f"🎉 Birthdays in {month_name}:\n\n" + "\n".join(
            f"{day}/{current_month}: {name}{' (@' + username + ')' if username else ''}"
            for day, name, username in month_birthdays
        )
    
    context.bot.send_message(chat_id=ADMIN_ID, text=message)

def schedule_monthly_report(updater):
    now = datetime.now()
    next_month = now.month % 12 + 1
    next_year = now.year + (1 if next_month == 1 else 0)
    next_report = datetime(next_year, next_month, 1, 9, 0)
    delay = (next_report - now).total_seconds()
    Timer(delay, lambda: [send_monthly_report(updater.dispatcher), schedule_monthly_report(updater)]).start()

def main():
    updater = Updater("7621821845:AAGGPOS6VpwXLDGsYvMaANaEAEVFTy3qYpg", use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("addbirthday", add_birthday))
    dp.add_handler(CommandHandler("mybirthday", my_birthday))
    dp.add_handler(CommandHandler("birthdaysthismonth", birthdays_this_month))
    
    updater.start_polling()
    schedule_monthly_report(updater)
    updater.idle()

if __name__ == '__main__':
    main()
