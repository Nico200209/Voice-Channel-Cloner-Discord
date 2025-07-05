from dotenv import load_dotenv
import os
load_dotenv()

import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

watched_channel_id = None  # ID of the channel to watch
separator_symbol = "-"     # Default separator
cloned_channels = {}       # Tracks all active clones

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔁 Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

@tree.command(name="clone", description="Set up a voice channel to auto-clone when joined.")
@app_commands.describe(
    channel="The voice channel to watch",
    separator="Optional: separator between channel name and user (default is '-')"
)
async def clone_command(
    interaction: discord.Interaction,
    channel: discord.VoiceChannel,
    separator: str = "-"
):
    global watched_channel_id, separator_symbol
    watched_channel_id = channel.id
    separator_symbol = separator if separator != "" else " "
    await interaction.response.send_message(
        f"✅ Now watching: `{channel.name}`\nSeparator set to: `{separator_symbol}`",
        ephemeral=True
    )

@bot.event
async def on_voice_state_update(member, before, after):
    global watched_channel_id, separator_symbol

    # User joined the watched channel
    if after.channel and after.channel.id == watched_channel_id:
        original = after.channel
        display_name = member.display_name
        new_name = f"{original.name}{separator_symbol}{display_name}"

        cloned = await original.clone(name=new_name)
        await cloned.edit(category=original.category)
        await member.move_to(cloned)

        cloned_channels[cloned.id] = {
            "original": original.name,
            "first_user": display_name
        }

    # If a user joins a clone that wasn't renamed yet (backup logic)
    if after.channel and after.channel.id in cloned_channels:
        info = cloned_channels[after.channel.id]
        if not info["first_user"]:
            info["first_user"] = member.display_name
            new_name = f"{info['original']}{separator_symbol}{member.display_name}"
            await after.channel.edit(name=new_name)

    # Delete cloned channel when empty
    if before.channel and before.channel.id in cloned_channels:
        if len(before.channel.members) == 0:
            await before.channel.delete()
            del cloned_channels[before.channel.id]

# Run the bot with your token from .env
bot.run(os.getenv("DISCORD_TOKEN"))