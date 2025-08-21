import discord
from discord import app_commands
import json
import os

# Load blacklist from file (or create empty)
BLACKLIST_FILE = "blacklist.json"
if os.path.exists(BLACKLIST_FILE):
    with open(BLACKLIST_FILE, "r") as f:
        blacklist = json.load(f)
else:
    blacklist = {}

def save_blacklist():
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(blacklist, f)

# Bot setup
intents = discord.Intents.default()
intents.members = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

@tree.command(name="smite", description="Ban a user and add them to the server's blacklist")
async def smite(interaction: discord.Interaction, member: discord.Member):
    guild_id = str(interaction.guild.id)

    if guild_id not in blacklist:
        blacklist[guild_id] = []

    if member.id not in blacklist[guild_id]:
        blacklist[guild_id].append(member.id)
        save_blacklist()
        await member.ban(reason=f"Smited by {interaction.user}")
        await interaction.response.send_message(f"⚡ {member.mention} has been smited and banned!")
    else:
        await interaction.response.send_message("That user is already on the blacklist.")

@tree.command(name="revive", description="Unban a user and remove them from the server's blacklist")
async def revive(interaction: discord.Interaction, member_id: str):
    guild_id = str(interaction.guild.id)

    if guild_id not in blacklist or int(member_id) not in blacklist[guild_id]:
        await interaction.response.send_message("That user is not blacklisted.")
        return

    blacklist[guild_id].remove(int(member_id))
    save_blacklist()

    banned_users = await interaction.guild.bans()
    for ban_entry in banned_users:
        user = ban_entry.user
        if str(user.id) == member_id:
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✨ {user.mention} has been revived and unbanned!")
            return

    await interaction.response.send_message("User was removed from blacklist but wasn’t banned.")

# Run the bot
bot.run(os.getenv("MTQwNzc3ODExNzcwNzEwNDI5Ng.GyggoP.3ErsLKTOGGhHgaR22M2YXrVutpwpjlXQ9p3Pcg"))
