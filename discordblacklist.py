import discord
from discord import app_commands
import json
import os
from dotenv import load_dotenv

# --- Load Environment Variables ---
# This line loads variables from a local .env file during development.
# On Render, the variables are provided directly by the platform.
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Configuration ---
# File to store the blacklist data
BLACKLIST_FILE = "blacklist.json"

# --- Blacklist Data Handling Functions ---
def save_blacklist(data):
    """Saves the blacklist data to a JSON file."""
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(data, f, indent=4) # Use indent for human-readable output

def load_blacklist():
    """
    Loads the blacklist from a JSON file.
    Initializes an empty dictionary if the file doesn't exist or is corrupted.
    """
    try:
        with open(BLACKLIST_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: {BLACKLIST_FILE} not found or is corrupted. Initializing empty blacklist.")
        return {}

# Load the blacklist on startup
blacklist = load_blacklist()

# --- Bot Setup ---
intents = discord.Intents.default()
intents.members = True # Required for member-related actions
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# --- Bot Events ---
@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# --- Slash Commands ---
@tree.command(
    name="smite",
    description="Ban a user and add them to the server's blacklist",
)
@app_commands.checks.has_permissions(ban_members=True)
async def smite(interaction: discord.Interaction, member: discord.Member):
    """Bans a user and adds them to the blacklist."""
    guild_id = str(interaction.guild.id)

    if guild_id not in blacklist:
        blacklist[guild_id] = []

    if member.id not in blacklist[guild_id]:
        blacklist[guild_id].append(member.id)
        save_blacklist(blacklist)
        
        try:
            await member.ban(reason=f"Smited by {interaction.user.name} ({interaction.user.id})")
            await interaction.response.send_message(f"⚡ {member.mention} has been smited and banned!")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban this user. The user might have a higher role.")
    else:
        await interaction.response.send_message("That user is already on the blacklist.")

@tree.command(
    name="revive",
    description="Unban a user and remove them from the server's blacklist",
)
@app_commands.checks.has_permissions(ban_members=True)
async def revive(interaction: discord.Interaction, member_id: str):
    """Unbans a user and removes them from the blacklist."""
    guild_id = str(interaction.guild.id)
    user_id = int(member_id)

    if guild_id not in blacklist or user_id not in blacklist[guild_id]:
        await interaction.response.send_message("That user is not blacklisted.")
        return

    # Remove the user from the blacklist
    blacklist[guild_id].remove(user_id)
    save_blacklist(blacklist)

    # Attempt to unban the user
    try:
        banned_users = await interaction.guild.bans()
        user_to_unban = discord.Object(id=user_id)
        await interaction.guild.unban(user_to_unban)
        await interaction.response.send_message(f"✨ User with ID `{user_id}` has been revived and unbanned!")
    except discord.NotFound:
        # This handles cases where the user was on the blacklist but not currently banned
        await interaction.response.send_message(f"User with ID `{user_id}` was removed from the blacklist but wasn’t found in the server's ban list.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to unban this user.")


# --- Error Handling for Slash Commands ---
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handles errors that occur within slash commands."""
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            f"🚫 You do not have permission to use this command. You need the following permissions: {', '.join(error.missing_permissions)}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"An unexpected error occurred: {error}",
            ephemeral=True
        )
        print(f"An unexpected error occurred: {error}")

# --- Run the bot ---
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable is not set.")
    else:
        bot.run(BOT_TOKEN)
