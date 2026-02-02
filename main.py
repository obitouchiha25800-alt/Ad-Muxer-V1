import os
import subprocess
from web import keep_alive

# 1. Start Web Server (Ping)
keep_alive()

# 2. Add FFmpeg to Linux PATH
if os.path.exists("bin/ffmpeg"):
    print("✅ FFmpeg found, adding to PATH...")
    os.environ["PATH"] += os.pathsep + os.path.abspath("bin")

# 3. Start your Bot
print("🚀 Starting Ad Muxer Bot...")
# Hum subprocess use kar rahe hain taaki bot crash hone par bhi server chalta rahe
subprocess.run(["python", "bot.py"])