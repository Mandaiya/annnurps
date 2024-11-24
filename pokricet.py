import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Game state
game_state = {
    "players": [],
    "current_player_index": 0,
    "balls_remaining": 6,
    "is_game_active": False,
    "game_creator_id": None,
    "timeout_task": None,
}

# Global player stats
player_stats = {}

# Constants for gameplay
RUNS = [1, 2, 4, 6]
DOT_BALLS = [3, 5, 9]

# Start Game Command
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts a new game and clears previous scores."""
    chat_id = update.effective_chat.id

    if game_state["is_game_active"]:
        await update.message.reply_text(
            "❗ A game is already in progress! Use /join to participate."
        )
        return

    game_state.update({
        "players": [],
        "current_player_index": 0,
        "is_game_active": False,
        "game_creator_id": update.effective_user.id,
        "balls_remaining": 6,
        "timeout_task": None,
    })

    await context.bot.send_message(
        chat_id=chat_id, text="📘 ** Book Cricket Game Started! Welcome to the BOOK CRICKET game ** \n\nPlayers can join using /join."
    )

# Join Game Command
async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allows players to join the game."""
    player_id = update.effective_user.id
    player_name = update.effective_user.first_name

    if any(player["id"] == player_id for player in game_state["players"]):
        await update.message.reply_text(f"❗ {player_name}, you're already in the game!")
        return

    game_state["players"].append({
        "id": player_id,
        "name": player_name,
        "score": 0,
        "is_out": False,
        "balls_assigned": 6,
    })

    if player_id not in player_stats:
        player_stats[player_id] = {
            "name": player_name,
            "total_score": 0,
            "games_played": 0,
            "games_won": 0,
            "games_lost": 0,
            "level": 1,
        }

    player_stats[player_id]["games_played"] += 1
    await update.message.reply_text(f"✅ {player_name} has joined the game!")

# Start Gameplay
async def open_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the game by assigning balls and notifying players."""
    chat_id = update.effective_chat.id
    if update.effective_user.id != game_state["game_creator_id"]:
        await update.message.reply_text("❗ Only the game creator can start the game.")
        return

    if len(game_state["players"]) < 2:
        await update.message.reply_text("❗ At least 2 players are needed to start the game.")
        return

    for player in game_state["players"]:
        player["balls_assigned"] = 6

    game_state["is_game_active"] = True

    player_list = ", ".join(player["name"] for player in game_state["players"])
    await update.message.reply_text(
        f"🎮 The Game is starting! \n\nEach player gets 6 balls for each round.\n\nPlayers: {player_list}\n\nUse /flip to start your turn."
    )

    await start_player_turn(update, context)

# Player's Turn
async def start_player_turn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the next player's turn."""
    chat_id = update.effective_chat.id

    while True:
        current_player = game_state["players"][game_state["current_player_index"]]
        if not current_player["is_out"]:
            break
        game_state["current_player_index"] = (game_state["current_player_index"] + 1) % len(game_state["players"])

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🎲 {current_player['name']}, \n\nit's your turn! Use /play to play your turn.",
    )

    if game_state["timeout_task"]:
        game_state["timeout_task"].cancel()
    game_state["timeout_task"] = asyncio.create_task(player_timeout(update, context, current_player))

async def player_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE, player: dict) -> None:
    """Handles timeout for inactive players."""
    await asyncio.sleep(60)
    chat_id = update.effective_chat.id
    if not player["is_out"]:
        player["is_out"] = True
        await context.bot.send_message(chat_id=chat_id, text=f"⏳ {player['name']} \n\ntimed out and is disqualified!")
        await end_player_turn(update, context)

# Play Function
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simulates a player's turn."""
    chat_id = update.effective_chat.id
    player_id = update.effective_user.id

    if not game_state["is_game_active"]:
        await update.message.reply_text("❗ The game hasn't started yet. \nUse /openbook to start the game.")
        return

    current_player = game_state["players"][game_state["current_player_index"]]
    if current_player["id"] != player_id:
        await update.message.reply_text(f"❗ Wait for your turn,\n {current_player['name']} is playing.")
        return

    page_number = random.randint(1, 400)
    last_digit = page_number % 10

    if last_digit == 0:
        current_player["is_out"] = True
        await update.message.reply_text(
            f"⚾ {current_player['name']} \n\nflipped to page {page_number} and is OUT!"
        )
    elif last_digit in DOT_BALLS:
        game_state["balls_remaining"] -= 1
        await update.message.reply_text(
            f"⚪ Dot ball! No runs scored.\n\nBalls left: {game_state['balls_remaining']}\n"
            f"\n📊 Current Score: {current_player['score']} runs."
        )
    else:
        score = random.choice(RUNS)
        current_player["score"] += score
        game_state["balls_remaining"] -= 1
        await update.message.reply_text(
            f"🏏 {current_player['name']} scored {score} runs! \n\nBalls left: {game_state['balls_remaining']}\n"
            f"\n📊 Total Score: {current_player['score']} runs."
        )

    if game_state["balls_remaining"] <= 0 or current_player["is_out"]:
        await end_player_turn(update, context)

# End Turn
async def end_player_turn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ends the current player's turn and starts the next."""
    game_state["balls_remaining"] = 6
    game_state["current_player_index"] = (game_state["current_player_index"] + 1) % len(game_state["players"])

    remaining_players = [player for player in game_state["players"] if not player["is_out"]]
    if len(remaining_players) == 1:
        winner = remaining_players[0]
        player_stats[winner["id"]]["total_score"] += winner["score"] + 10  # Award 10 bonus points for winning
        player_stats[winner["id"]]["games_won"] += 1
        player_stats[winner["id"]]["level"] += 1  # Advance to the next level
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🎉 {winner['name']} \n\nwins with {winner['score']} runs! \n\n🎯 Level Up: {player_stats[winner['id']]['level']}"
        )
        for player in game_state["players"]:
            if player != winner:
                player_stats[player["id"]]["total_score"] -= 5  # Deduct points for losing
                player_stats[player["id"]]["games_lost"] += 1
                player_stats[player["id"]]["level"] = 1  # Reset level for losing
        game_state["is_game_active"] = False
        return

    await start_player_turn(update, context)

# Close Game Command
async def close_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ends the game if initiated by a participant."""
    player_id = update.effective_user.id

    if player_id not in [player["id"] for player in game_state["players"]]:
        await update.message.reply_text("❗ You are not part of the game and cannot close it.")
        return

    game_state["is_game_active"] = False
    await update.message.reply_text("🛑 The game has been closed.")

# Statsbook Command
async def stats_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays statistics for all players."""
    if not player_stats:
        await update.message.reply_text("📋 No player stats available yet!")
        return

    stats_message = "📊 ** Player Statistics **:\n"
    for stats in player_stats.values():
        stats_message += (
            f"👤 {stats['name']}:\n"
            f"🏏 - Games Played: {stats['games_played']}\n"
            f"🕹 - Games Won: {stats['games_won']}\n"
            f"🗽 - Games Lost: {stats['games_lost']}\n"
            f"🎼 - Total Score: {stats['total_score']}\n"
            f"🎚  - Level: {stats['level']}\n\n"
        )

    await update.message.reply_text(stats_message)

# Help Command
async def help_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays a list of available commands."""
    await update.message.reply_text(
        "📖 **Book Cricket Commands**:\n\n"
        "1. `/startbook` - Start a new game.\n"
        "2. `/join` - Join an ongoing game.\n"
        "3. `/openbook` - Start the match (Creator only).\n"
        "4. `/flip` - Play your turn.\n"
        "5. `/closebook` - Close the game.\n"
        "6. `/statsbook` - Display player statistics.\n"
        "7. `/helpbook` - Display this help message."
    )

# Main function
def main() -> None:
    """Run the bot."""
    application = Application.builder().token("7784540622:AAHN7M3-475DMj8GHUbcxyUhDsdktScrMQQ").build()

    application.add_handler(CommandHandler("startbook", start_book))
    application.add_handler(CommandHandler("join", join_game))
    application.add_handler(CommandHandler("openbook", open_book))
    application.add_handler(CommandHandler("flip", flip))
    application.add_handler(CommandHandler("closebook", close_book))
    application.add_handler(CommandHandler("statsbook", stats_book))
    application.add_handler(CommandHandler("helpbook", help_book))

    application.run_polling()

if __name__ == "__main__":
    main()
