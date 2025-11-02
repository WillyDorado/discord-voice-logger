import discord
from discord.ext import commands
import datetime
import traceback
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
TOKEN = os.getenv("TOKEN")

# --- CONFIG ---
LOG_CHANNEL_ID = 809117798164594689  # canal de logs
LOG_FILE = "voice_log.txt"

# --- INTENTS ---
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
active_sessions = {}

# --- FUNCIONES AUXILIARES ---
async def log_message(message, log_channel=None, duration=None,
                      member=None, channel_name=None,
                      join_time=None, leave_time=None):
    os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
        if duration is not None:
            f.write(
                f"  • User: {member}\n"
                f"  • Channel: {channel_name}\n"
                f"  • Joined: {join_time.strftime('%H:%M:%S UTC')}\n"
                f"  • Left: {leave_time.strftime('%H:%M:%S UTC')}\n"
                f"  • Duration: {int(duration)} seconds\n\n"
            )
    if log_channel:
        try:
            await log_channel.send(message)
        except Exception as e:
            print(f"⚠️ Could not send log to channel: {e}")

# --- EVENTO: BOT LISTO ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    if LOG_CHANNEL_ID:
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            print(f"📜 Logging to channel ID: {LOG_CHANNEL_ID}")
            try:
                await log_channel.send("✅ Bot is now online and ready to log voice activity!")
            except Exception as e:
                print(f"⚠️ Could not send message to log channel: {e}")
        else:
            print("⚠️ Could not find log channel! Check LOG_CHANNEL_ID or permissions.")
    else:
        print("📁 Logging only to file (no Discord channel set).")

# --- EVENTO: VOICE STATE UPDATE ---
@bot.event
async def on_voice_state_update(member, before, after):
    print(f"[DEBUG] Voice event triggered for {member.display_name}")
    try:
        log_channel = bot.get_channel(LOG_CHANNEL_ID) if LOG_CHANNEL_ID else None
        # --- JOIN ---
        if before.channel is None and after.channel is not None:
            join_time = datetime.datetime.utcnow()
            active_sessions[member.id] = (after.channel.id, join_time)
            msg = f"🎤 {member.display_name} **joined** {after.channel.name} at {join_time.strftime('%H:%M:%S UTC')}"
            print(msg)
            await log_message(msg, log_channel)
        # --- LEAVE ---
        elif before.channel is not None and after.channel is None:
            leave_time = datetime.datetime.utcnow()
            if member.id in active_sessions:
                channel_id, join_time = active_sessions.pop(member.id)
                duration = (leave_time - join_time).total_seconds()
                duration_str = f"{int(duration // 60)}m {int(duration % 60)}s"
                if duration < 120:
                    msg = f"🚨 {member.display_name} left {before.channel.name} after only **{duration_str}**!"
                else:
                    msg = f"✅ {member.display_name} left {before.channel.name} — stayed for **{duration_str}**."
                print(msg)
                await log_message(msg, log_channel, duration, member, before.channel.name, join_time, leave_time)
        # --- SWITCH CHANNEL ---
        elif before.channel != after.channel:
            leave_time = datetime.datetime.utcnow()
            if member.id in active_sessions:
                channel_id, join_time = active_sessions.pop(member.id)
                duration = (leave_time - join_time).total_seconds()
                duration_str = f"{int(duration // 60)}m {int(duration % 60)}s"
                if duration < 120:
                    msg = f"🔁🚨 {member.display_name} switched from {before.channel.name} → {after.channel.name} after only **{duration_str}**!"
                else:
                    msg = f"🔁 {member.display_name} moved from {before.channel.name} → {after.channel.name} (stayed **{duration_str}**)"
                print(msg)
                await log_message(msg, log_channel, duration, member, before.channel.name, join_time, leave_time)
            active_sessions[member.id] = (after.channel.id, leave_time)
    except Exception as e:
        print("⚠️ Error in on_voice_state_update:", e)
        traceback.print_exc()

# --- INICIAR BOT ---
print(f"TOKEN loaded? {'Yes' if TOKEN else 'No'}")

# --- Ejecutar el bot con auto-reinicio ---
async def run_bot():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print(f"⚠️ Bot crashed with error: {e}. Restarting in 10 seconds...")
            await asyncio.sleep(10)

asyncio.run(run_bot())
