import logging
import random
import requests

# Define the bot token directly in the script
BOT_TOKEN = '6991024540:AAFeaNbThwfbR8i82SLyrT8tjS5VZjIimk4'  # Replace 'YOUR_BOT_TOKEN' with your actual bot token

# Enable logging
logging.basicConfig(level=logging.INFO)

# Define the base URL for the Telegram Bot API
BASE_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

# Define game state for each user and an overall game activation state
user_games = {}
game_active = True  # Global flag to track if the game is active

# Helper function to send messages with user name in bold
def send_message(chat_id, user_id, text, username=None):
    if username:
        mention = f"*{username}*"
    else:
        mention = f"*User-{user_id}*"
    
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"{mention}, {text}", "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# Game logic for Rock, Paper, Scissors
def play_rps(user_choice, game_state):
    bot_choice = random.choice(['rock', 'paper', 'scissors'])
    
    if user_choice == bot_choice:
        result = "It's a tie! No points awarded."
    elif (user_choice == 'rock' and bot_choice == 'scissors') or \
         (user_choice == 'scissors' and bot_choice == 'paper') or \
         (user_choice == 'paper' and bot_choice == 'rock'):
        game_state['user_score'] += 1
        result = "You win this round!"
    else:
        game_state['bot_score'] += 1
        result = "Bot wins this round!"
    
    if game_state['user_score'] >= game_state['target_score']:
        final_message = f"You chose {user_choice}, bot chose {bot_choice}. {result}\n\n🎉 Congratulations! You won the game with a score of {game_state['user_score']} - {game_state['bot_score']}.\n\nType /startrps to play another match."
        update_scoreboard(game_state['username'], game_state['user_score'])
        reset_game(game_state)
        return final_message
    elif game_state['bot_score'] >= game_state['target_score']:
        final_message = f"You chose {user_choice}, bot chose {bot_choice}. {result}\n\n😢 The bot won the game with a score of {game_state['bot_score']} - {game_state['user_score']}.\n\nType /startrps to play another match."
        reset_game(game_state)
        return final_message
    else:
        return f"You chose {user_choice}, bot chose {bot_choice}. {result}\nScore: You {game_state['user_score']} - Bot {game_state['bot_score']}"

# Function to reset the game state for a user after a game ends
def reset_game(game_state):
    game_state['user_score'] = 0
    game_state['bot_score'] = 0
    game_state['target_score'] = None
    game_state['setting_target'] = True
    game_state['active'] = False

# Initialize scoreboard to track each user's cumulative points
scoreboard = {}

# Function to update the scoreboard
def update_scoreboard(username, points):
    if username in scoreboard:
        scoreboard[username] += points
    else:
        scoreboard[username] = points

# Function to display the scoreboard
def display_scoreboard(chat_id):
    if not scoreboard:
        send_message(chat_id, None, "No scores yet. Start a game with /startrps!")
        return
    
    scoreboard_text = "📊 *Scoreboard*\n\n"
    for user, score in scoreboard.items():
        scoreboard_text += f"{user}: {score} points\n"
    
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": scoreboard_text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# Polling function to fetch new messages
def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    response = requests.get(url, params=params)
    return response.json()["result"]

# Handle each update
def handle_update(update):
    global game_active

    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    username = message["from"].get("username", None)
    text = message.get("text", "").lower()
    
    # Initialize game state for a new user
    if user_id not in user_games:
        user_games[user_id] = {'user_score': 0, 'bot_score': 0, 'target_score': None, 'setting_target': False, 'active': False, 'username': username}

    game_state = user_games[user_id]
    
    if text == "/start":
        send_message(chat_id, user_id, "🎮 A new game called *Rock : Paper : Scissors* is available! To play, type /startrps.", username)
    
    elif text == "/startrps":
        # Start a new game for the user and activate the game globally
        reset_game(game_state)
        game_state['active'] = True
        game_active = True
        send_message(chat_id, user_id, "Please enter a target score between 1 and 10 to start your game.", username)
    
    elif text == "/stoprps":
        # Deactivate the game globally
        game_active = False
        user_games.clear()
        send_message(chat_id, user_id, "Rock, Paper, Scissors game has ended for everyone.", username)
    
    elif text == "/scoreboard":
        display_scoreboard(chat_id)
    
    elif text == "/help":
        # Provide instructions on available commands
        help_text = (
            "*Available Commands:*\n\n"
            "/start - Start a conversation with the bot.\n"
            "/startrps - Begin a new Rock, Paper, Scissors game.\n"
            "/stoprps - Stop the game for everyone.\n"
            "/scoreboard - Display the current scoreboard.\n"
            "/help - Show this help message.\n\n"
            "*How to Play:*\n"
            "1. Type /startrps to start a game.\n"
            "2. Set a target score between 1 and 10.\n"
            "3. Enter your choice: 'rock', 'paper', or 'scissors'.\n"
            "4. First to reach the target score wins the game!"
        )
        send_message(chat_id, user_id, help_text, username)
    
    elif game_state['setting_target']:
        try:
            target_score = int(text)
            if 1 <= target_score <= 10:
                game_state['target_score'] = target_score
                game_state['setting_target'] = False
                send_message(chat_id, user_id, f"Great! First to reach {target_score} points wins. \nYou can start by typing 'rock', 'paper', or 'scissors'.", username)
            else:
                send_message(chat_id, user_id, "Invalid target score. Please enter a number between 1 and 10.", username)
        except ValueError:
            send_message(chat_id, user_id, "Invalid input. Please enter a number between 1 and 10.", username)
    
    elif text in ["rock", "paper", "scissors"]:
        if not game_state['active']:
            send_message(chat_id, user_id, "You are not entered into the game. Type '/startrps' to join.", username)
        elif game_state['target_score'] is None:
            send_message(chat_id, user_id, "Please start a new game and set a target score by typing '/startrps'.", username)
        else:
            result_message = play_rps(text, game_state)
            send_message(chat_id, user_id, result_message, username)

# Main polling loop
def main():
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates:
            handle_update(update)
            offset = update["update_id"] + 1

if __name__ == "__main__":
    main()
