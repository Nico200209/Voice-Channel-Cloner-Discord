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

watched_channels = {}   # channel_id: separator
cloned_channels = {}    # cloned_id: {original, first_user, separator}

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
    separator="Optional: Separator between channel name and user"
)
async def clone_command(
    interaction: discord.Interaction,
    channel: discord.VoiceChannel,
    separator: str = " "
):
    clean_separator = separator.replace("_", " ") if separator else " "
    watched_channels[channel.id] = clean_separator

    await interaction.response.send_message(
        f"✅ Now watching: `{channel.name}`\nSeparator set to: `{clean_separator}`",
        ephemeral=True
    )

@bot.event
async def on_voice_state_update(member, before, after):
    # User joins a watched channel
    if after.channel and after.channel.id in watched_channels:
        original = after.channel
        separator = watched_channels[original.id]
        new_name = f"{original.name}{separator}{member.display_name}"

        cloned = await original.clone(name=new_name)
        await cloned.edit(category=original.category)
        await member.move_to(cloned)

        cloned_channels[cloned.id] = {
            "original": original.name,
            "first_user": member.display_name,
            "separator": separator
        }

    # If user joins a cloned channel without name set
    if after.channel and after.channel.id in cloned_channels:
        info = cloned_channels[after.channel.id]
        if not info["first_user"]:
            info["first_user"] = member.display_name
            new_name = f"{info['original']}{info['separator']}{member.display_name}"
            await after.channel.edit(name=new_name)

    # Delete empty clones
    if before.channel and before.channel.id in cloned_channels:
        if len(before.channel.members) == 0:
            await before.channel.delete()
            del cloned_channels[before.channel.id]

bot.run(os.getenv("DISCORD_TOKEN"))