import json
import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
load_dotenv('keys.env')

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
api_key = os.getenv('api_key')
token = os.getenv('token')
headers = {"X-Riot-Token": api_key}

def get_puuid_by_name_tagline(name, tagline):
    
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tagline}?api_key={api_key}"
    
    print(f"Request URL: {url}")  
    response = requests.get(url, headers=headers)

    print(f"Response Status: {response.status_code}")  
    if response.status_code == 200:
        response_data = response.json()  
        print(f"Full Response Data: {response_data}")  
        return response_data.get("puuid")  
    else:
        print(f"Error: {response.status_code} - {response.text}")  
        return f"Error: {response.status_code} - {response.text}"

@bot.command()
async def get_puuid(ctx, name: str, tagline: str):
    puuid = get_puuid_by_name_tagline(name, tagline)
    
    if isinstance(puuid, str) and puuid.startswith("Error"):
        await ctx.send(puuid)
        return
    
    await ctx.send(f"The PUUID for {name}#{tagline} is: {puuid}")
    
    user_id = str(ctx.author.id)
    
    stats = load_stats()
    
    
    if user_id not in stats:
        stats[user_id] = {}
    
    
    if 'puuid' not in stats[user_id]:
        stats[user_id]['puuid'] = puuid
    
    save_stats(stats)
    
    await ctx.send(f"Your PUUID has been saved successfully.")

def get_match_ids(puuid):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=20&api_key={api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error fetching match IDs: {response.status_code} - {response.text}"

def get_match_stats(match_id):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json() 
    else:
        return f"Error fetching match stats: {response.status_code} - {response.text}"

def get_total_mastery_score(puuid):
    url = f"https://na1.api.riotgames.com/lol/champion-mastery/v4/scores/by-puuid/{puuid}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json() 
    else:
        return f"Error fetching total mastery: {response.status_code} - {response.text}"

@bot.command()
async def total_mastery(ctx, name: str, tagline: str):
    
    puuid = get_puuid_by_name_tagline(name, tagline)
    
    if isinstance(puuid, str) and puuid.startswith("Error"):
        await ctx.send(puuid)  
        return
    
    
    mastery_score = get_total_mastery_score(puuid)
    
    if isinstance(mastery_score, str) and mastery_score.startswith("Error"):
        await ctx.send(mastery_score)
    else:
        
        await ctx.send(f"{name}#{tagline} has a total mastery score of: {mastery_score}")

def load_stats():
    try:
        with open("stats.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_stats(stats):
    with open("stats.json","w") as file:
        json.dump(stats, file, indent=4)

@bot.event
async def on_ready():
    print("Bot ready!")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! I'm the Stat Sage!")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

game_stats = {
    "League": ["Kills", "Deaths", "Wins", "Losses", "Assists"],
    "Deadlock": ["Kills", "Deaths", "Wins", "Losses", "Assists", "Souls"]
}

deadlock_characters = ["Abrams","Bebop","Dynamo","Grey Talon", "Haze", "Infernus", "Ivy", "Kelvin", "Lady Geist", "Lash", "McGinnis", "Mirage", "Mo & Krill", "Paradox", "Pocket", "Seven", "Shiv", "Vindicta", "Viscous", "Warden", "Wraith", "Yamato"]

league_stat_order = ["Kills", "Deaths", "Assists", "Wins", "Losses"]

deadlock_stat_order = ["Kills", "Deaths", "Assists", "Wins", "Losses", "Souls"]

@bot.command()
async def update_stat(ctx, game_name: str, character_name: str, stat_name: str, stat_value: int):
    stats = load_stats()
    user_id = str(ctx.author.id)

    game_name = game_name.capitalize()
    character_name = character_name.capitalize()

    valid_games = ["Deadlock", "League"]

    if game_name not in valid_games:
        await ctx.send(f"Invalid game name. Valid games are: {', '.join(valid_games)}.")
        return

    if game_name == "Deadlock":
        if character_name not in deadlock_characters:
            await ctx.send(f"Invalid character name. Please choose a valid Deadlock character: {', '.join(deadlock_characters)}.")
            return

    if user_id not in stats:
        stats[user_id] = {}

    if game_name not in stats[user_id]:
        stats[user_id][game_name] = {}

    if character_name not in stats[user_id][game_name]:
        stats[user_id][game_name][character_name] = {}

    if stat_name.capitalize() not in game_stats.get(game_name, []):
        await ctx.send(f"Invalid stat name for {game_name}. Valid stats are: {', '.join(game_stats.get(game_name, []))}.")
        return

    stat_name = stat_name.strip().capitalize()

    stats[user_id][game_name][character_name][stat_name] = stat_value
    save_stats(stats)

    await ctx.send(f"Updated {ctx.author.name}'s {character_name} ({game_name}) {stat_name} to {stat_value}!")

@bot.command()
async def view_stats(ctx, game_name: str = None):
    stats = load_stats()
    user_id = str(ctx.author.id)

    if user_id not in stats:
        await ctx.send("You don't have any recorded stats yet.")
        return

    
    stat_message = ""

    if game_name is None:  
        for game in stats[user_id]:  
            stat_message += f"**{game} Stats:**\n"
            stat_order = league_stat_order if game == "League" else deadlock_stat_order
            for character_name, character_stats in stats[user_id][game].items():
                character_stat_message = ", ".join([f"{stat}: {character_stats.get(stat, 'Not recorded')}" for stat in stat_order])
                stat_message += f"{character_name}: {character_stat_message}\n"
            stat_message += "\n"  
    else:
        game_name = game_name.capitalize()
        if game_name not in stats[user_id]:
            await ctx.send(f"You have no recorded stats for {game_name}.")
            return

        stat_message += f"**{game_name} Stats:**\n"
        stat_order = league_stat_order if game_name == "League" else deadlock_stat_order
        for character_name, character_stats in stats[user_id][game_name].items():
            character_stat_message = ", ".join([f"{stat}: {character_stats.get(stat, 'Not recorded')}" for stat in stat_order])
            stat_message += f"{character_name}: {character_stat_message}\n"

    if stat_message:
        await ctx.send(stat_message)
    else:
        await ctx.send("No stats available.")

@bot.command()
async def view_stats_all(ctx, game_name: str = None):
    stats = load_stats()
    user_id = str(ctx.author.id)
    
    if user_id not in stats:
        await ctx.send(f"{ctx.author.name}, you don't have any recorded stats yet.")
        return

    stat_message = ""

    if game_name:
        game_name = game_name.capitalize()
        if game_name not in stats[user_id]:
            await ctx.send(f"No stats found for {game_name}.")
            return

        combined_stats = {}
        stat_order = league_stat_order if game_name == "League" else deadlock_stat_order

        for character_name, character_stats in stats[user_id][game_name].items():
            for stat in stat_order:
                combined_stats[stat] = combined_stats.get(stat, 0) + character_stats.get(stat, 0)

        stat_message += f"**{game_name} Combined Stats:**\n"
        for stat in stat_order:
            stat_message += f"{stat}: {combined_stats.get(stat, 'Not recorded')}\n"
    else:
        for game in stats[user_id]:
            combined_stats = {}
            stat_order = league_stat_order if game == "League" else deadlock_stat_order

            for character_name, character_stats in stats[user_id][game].items():
                for stat in stat_order:
                    combined_stats[stat] = combined_stats.get(stat, 0) + character_stats.get(stat, 0)

            stat_message += f"**{game} Combined Stats:**\n"
            for stat in stat_order:
                stat_message += f"{stat}: {combined_stats.get(stat, 'Not recorded')}\n"
            stat_message += "\n"

    await ctx.send(stat_message)

@bot.command()
async def leaderboard(ctx, game_name: str, character_name: str = None):
    stats = load_stats()
    leaderboard_data = {}

    valid_games = ["Deadlock", "League"]
    game_name = game_name.capitalize() 

    if game_name not in valid_games:
        await ctx.send(f"Invalid game name. Valid games are: {', '.join(valid_games)}.")
        return

    
    for user_id, user_stats in stats.items():
        if game_name in user_stats:
            for character, character_stats in user_stats[game_name].items():
                
                if character_name is None or character_name.capitalize() == character:
                    for stat in (league_stat_order if game_name == "League" else deadlock_stat_order):
                        if stat not in leaderboard_data:
                            leaderboard_data[stat] = {}
                        if user_id not in leaderboard_data[stat]:
                            leaderboard_data[stat][user_id] = 0
                        leaderboard_data[stat][user_id] += character_stats.get(stat, 0)

    
    if not leaderboard_data:
        await ctx.send(f"No stats available for the character '{character_name}' in {game_name}.")
        return

    
    leaderboard_message = f"**{game_name} Leaderboard**\n"

    
    for stat in (league_stat_order if game_name == "League" else deadlock_stat_order):
        if stat in leaderboard_data:
            sorted_scores = sorted(leaderboard_data[stat].items(), key=lambda x: x[1], reverse=True)
            leaderboard_message += f"\n**{stat}**:\n"
            for user_id, score in sorted_scores[:10]:
                user = await bot.fetch_user(user_id)  
                leaderboard_message += f"{user.name}: {score if score > 0 else 'Not recorded'}\n"

    await ctx.send(leaderboard_message)

@bot.command(name='commands')
async def commands(ctx):
    commands_list = {
        ".view_stats": "View your character's stats.",
        ".view_all_stats": "View all recorded stats for your characters.",
        ".leaderboard [game_name] [character_name]": "Show the leaderboard for a specific game and character.",
        ".add_stats [game_name] [character_name] [stat_name] [value]": "Add or update stats for a character.",
        ".commands": "Show this help message.",
        ".ping": "Has the bot respond back with Pong!",
        ".hello": "Has the bot say hello back.",
        ".get_puuid [name] [tagline]": "Shows and sets your puuid for League by typing in your in game name and tag. Used for other commands requiring puuid.",
        ".total_mastery [name] [tagline]": "Shows your current total mastery across all champions in League."
    }

    help_message = "**Available Commands:**\n"
    for command, description in commands_list.items():
        help_message += f"{command} - {description}\n"

    await ctx.send(help_message)

bot.run(token)