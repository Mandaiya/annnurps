from pyrogram import Client, filters
from datetime import datetime
import os

# Replace 'YOUR_API_KEY' with your BotFather bot token or use environment variables
API_KEY = os.getenv("7621821845:AAGGPOS6VpwXLDGsYvMaANaEAEVFTy3qYpg") or "YOUR_API_KEY"

# Initialize the bot
app = Client("birthday_bot", bot_token=API_KEY)

# Dictionary to store birthdays
birthdays = {}

@app.on_message(filters.command("start"))
def start(client, message):
    message.reply_text("Hello! I can help you track birthdays. Use /add_birthday to add your birthday and /get_birthdays to find birthdays in a specific month.")

@app.on_message(filters.command("add_birthday"))
def add_birthday(client, message):
    try:
        # Extract user ID and birthday
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        text = message.text.split(maxsplit=1)
        
        if len(text) < 2:
            message.reply_text("Please provide your birthday in DD-MM format, e.g., `/add_birthday 15-04`.")
            return
        
        birthday_str = text[1]
        birthday = datetime.strptime(birthday_str, "%d-%m")
        
        # Store the birthday
        birthdays[user_id] = {"name": user_name, "date": birthday}
        message.reply_text(f"Thank you! Your birthday has been saved as {birthday.strftime('%d-%B')}.")
    except Exception as e:
        message.reply_text("Invalid format! Please use DD-MM format, e.g., `/add_birthday 15-04`.")

@app.on_message(filters.command("get_birthdays"))
def get_birthdays(client, message):
    try:
        # Extract month from the user's query
        text = message.text.split(maxsplit=1)
        
        if len(text) < 2:
            message.reply_text("Please provide a month number (1-12), e.g., `/get_birthdays 4`.")
            return
        
        month = int(text[1])
        if month < 1 or month > 12:
            message.reply_text("Invalid month number! Please provide a number between 1 and 12.")
            return
        
        # Get all birthdays in the specified month
        result = []
        for user_id, info in birthdays.items():
            if info["date"].month == month:
                result.append(f"{info['name']} - {info['date'].strftime('%d-%B')}")
        
        if result:
            message.reply_text(f"Birthdays in month {month}:\n" + "\n".join(result))
        else:
            message.reply_text(f"No birthdays found for month {month}.")
    except Exception as e:
        message.reply_text("An error occurred while processing your request.")

# Run the bot
if __name__ == "__main__":
    if API_KEY == "7621821845:AAGGPOS6VpwXLDGsYvMaANaEAEVFTy3qYpg":
        print("Error: Please replace 'YOUR_API_KEY' with your actual Telegram bot token or set it as an environment variable.")
    else:
        app.run()
