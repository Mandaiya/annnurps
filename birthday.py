import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import calendar
import sqlite3

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

# Initialize the database
init_db()

# Admin ID
ADMIN_ID = 655594746  # Replace with your Telegram user ID

# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎉 Welcome to the Birthday Calendar Bot! 🎉\n\n"
        "Use /addbirthday DD MM to add your birthday\n"
        "Use /mybirthday to check your stored birthday\n"
        "Admins: /birthdaysthismonth to see this month's birthdays"
    )

# Command: Add Birthday
async def add_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    args = context.args

    if not args or len(args) != 2:
        await update.message.reply_text("Usage: /addbirthday DD MM (e.g., /addbirthday 15 04)")
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
        await update.message.reply_text(f"🎂 Birthday saved! We'll remember you on {day}/{month}.")
    except ValueError as e:
        await update.message.reply_text(f"Error: {e}\nUsage: /addbirthday DD MM")

# Command: My Birthday
async def my_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    birthdays = load_birthdays()

    if user.id in birthdays:
        bday = birthdays[user.id]
        await update.message.reply_text(f"Your birthday: {bday['day']}/{bday['month']}.")
    else:
        await update.message.reply_text("You haven't added your birthday yet. Use /addbirthday DD MM.")

# Command: Birthdays This Month
async def birthdays_this_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if ADMIN_ID and update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return

    current_month = datetime.now().month
    birthdays = load_birthdays()

    month_birthdays = [
        (bday['day'], bday['name'], bday.get('username', ''))
        for bday in birthdays.values()
        if bday['month'] == current_month
    ]

    if not month_birthdays:
        await update.message.reply_text("No birthdays this month!")
        return

    month_birthdays.sort()
    response = "🎉 Birthdays this month:\n\n" + "\n".join(
        f"{day}/{current_month}: {name}{' (@' + username + ')' if username else ''}"
        for day, name, username in month_birthdays
    )
    await update.message.reply_text(response)

# Main function
def main():
    app = ApplicationBuilder().token("7621821845:AAGGPOS6VpwXLDGsYvMaANaEAEVFTy3qYpg").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addbirthday", add_birthday))
    app.add_handler(CommandHandler("mybirthday", my_birthday))
    app.add_handler(CommandHandler("birthdaysthismonth", birthdays_this_month))

    print("Bot is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
