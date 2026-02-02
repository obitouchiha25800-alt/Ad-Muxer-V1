import os
import subprocess
import time
import asyncio
import socket
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

# --- CONFIG ---
API_ID = 10826472
API_HASH = "da41e7d76e4df7f7d46c5ea6a9229167"
BOT_TOKEN = "8599256568:AAFMOiM9fbzBtyN6qUZP01p4wIdM676mhko"
OWNER_USERNAME = "RealLifeObito"
ADMIN_ID = 2096201372

# --- AUTO DETECT FFMPEG ---
if os.path.exists("ffmpeg.exe"):
    FFMPEG_CMD = "ffmpeg.exe"
else:
    FFMPEG_CMD = "ffmpeg"

# --- LOCAL IP HELPER ---
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# --- BOT SETUP ---
app = Client("ad_mux_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- FOLDERS ---
FONTS_DIR = "Permanent_Fonts"
BASE_FONT_DIR = "User_Fonts"
DOWNLOADS_DIR = "downloads"
ACCESS_FILE = "allowed_users.txt"

for d in [FONTS_DIR, BASE_FONT_DIR, DOWNLOADS_DIR]:
    os.makedirs(d, exist_ok=True)

if not os.path.exists(ACCESS_FILE): 
    with open(ACCESS_FILE, "w") as f: f.write(str(ADMIN_ID) + "\n")

user_data = {}

# Steps
STEP_VIDEO = 1
STEP_FONT_DECISION = 2
STEP_SUBTITLE = 3
STEP_NAME = 4

# --- KEEP ALIVE SERVER ---
routes = web.RouteTableDef()
@routes.get("/", allow_head=True)
async def root_route(request): return web.json_response({"status": "Bot is Alive", "owner": OWNER_USERNAME})

async def web_server():
    web_app = web.Application()
    web_app.add_routes(routes)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

# --- HELPERS ---
def check_access(user_id):
    if user_id == ADMIN_ID: return True
    if os.path.exists(ACCESS_FILE):
        with open(ACCESS_FILE, "r") as f: return str(user_id) in f.read().splitlines()
    return False

def grant_access(user_id):
    with open(ACCESS_FILE, "a") as f: f.write(f"{user_id}\n")

def revoke_access(user_id):
    if not os.path.exists(ACCESS_FILE): return
    with open(ACCESS_FILE, "r") as f: lines = f.readlines()
    with open(ACCESS_FILE, "w") as f:
        for line in lines:
            if line.strip() != str(user_id):
                f.write(line)

def get_authorized_users():
    if not os.path.exists(ACCESS_FILE): return []
    with open(ACCESS_FILE, "r") as f:
        return [u.strip() for u in f.readlines() if u.strip() and u.strip() != str(ADMIN_ID)]

def get_user_font_dir(user_id):
    path = os.path.join(BASE_FONT_DIR, str(user_id))
    os.makedirs(path, exist_ok=True)
    return path

async def progress(current, total, message, start_time):
    now = time.time()
    if (now - start_time) > 5 or current == total:
        percent = 100 * (current / total)
        try: await message.edit_text(f"⬇️ **Downloading...**\n📊 {percent:.1f}% Complete")
        except: pass

# --- UI KEYBOARDS ---
def get_start_kb(user_id):
    btns = [
        [InlineKeyboardButton("📂 My Fonts", callback_data="manage_fonts")],
        [InlineKeyboardButton("📚 Guide", callback_data="help_menu")]
    ]
    if user_id == ADMIN_ID:
        btns.append([InlineKeyboardButton("🛡️ Admin Panel", callback_data="admin_panel")])
        
    btns.append([
        InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{OWNER_USERNAME}"), 
        InlineKeyboardButton("📞 Contact", url=f"https://t.me/{OWNER_USERNAME}")
    ])
    return InlineKeyboardMarkup(btns)

async def ask_font_decision(client, message, user_id):
    user_dir = get_user_font_dir(user_id)
    saved_fonts = [f for f in os.listdir(user_dir) if f.endswith(('.ttf', '.otf'))]
    count = len(saved_fonts)
    
    if count > 0:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📂 Use Saved Fonts ({count})", callback_data="use_saved_fonts")],
            [InlineKeyboardButton("➕ Upload New Font", callback_data="upload_new_font")],
            [InlineKeyboardButton("⏭️ Skip Fonts", callback_data="skip_fonts")]
        ])
        await message.reply_text(f"✅ **Received!**\n\nYou have **{count} fonts** saved.\nWhat do you want to do?", reply_markup=kb)
    else:
        user_data[user_id]["step"] = STEP_FONT_DECISION
        await message.reply_text("✅ **Received!**\n\n🔤 **No saved fonts.**\nSend a **.ttf/.otf** to save one.\nOR send **Subtitle (.ass)** to skip.")

async def show_font_selection(client, message, user_id):
    user_dir = get_user_font_dir(user_id)
    fonts = [f for f in os.listdir(user_dir) if f.endswith(('.ttf', '.otf'))]
    selected = user_data[user_id].get("fonts", [])
    
    btns = []
    for f in fonts:
        mark = "✅" if f in selected else ""
        btns.append([InlineKeyboardButton(f"{mark} {f}", callback_data=f"toggle_{f}")])
    btns.append([InlineKeyboardButton("💾 DONE & NEXT ➡️", callback_data="fonts_selected_done")])
    try: await message.edit_reply_markup(InlineKeyboardMarkup(btns))
    except: await message.reply_text("🔤 **Select Fonts:**", reply_markup=InlineKeyboardMarkup(btns))

# --- COMMANDS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    if not check_access(user_id):
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔑 Request Access", callback_data="req_access")]])
        await message.reply_text(f"🔒 **Access Restricted!**\n\nHello {first_name}, you do not have permission to use this bot.\nContact the owner.", reply_markup=kb)
        return
    
    user_data[user_id] = {"step": STEP_VIDEO, "fonts": []}
    user_dir = get_user_font_dir(user_id)
    font_count = len([f for f in os.listdir(user_dir) if f.endswith(('.ttf', '.otf'))])
    
    text = (
        f"**AD Muxing Bot** 🛡️\n\n"
        f"👋 **Hello, {first_name}**\n\n"
        f"🔹 **Status:** Operational\n"
        f"🔹 **Fonts:** {font_count} Saved\n\n"
        f"🚀 **Ready to Mux**\n"
        f"Send a **Video File** or **Link** to begin."
    )
    await message.reply_text(text, reply_markup=get_start_kb(user_id))

# --- CALLBACKS ---
@app.on_callback_query()
async def callbacks(client, query):
    data = query.data
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    user_dir = get_user_font_dir(user_id)
    
    if data == "req_access":
        await query.message.edit_text("⏳ **Request Sent!**\nWait for Admin approval.")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")],
            [InlineKeyboardButton("❌ Deny", callback_data=f"deny_{user_id}")]
        ])
        await client.send_message(ADMIN_ID, f"🚨 **New Access Request**\nUser: {first_name}\nID: `{user_id}`", reply_markup=kb)
    
    elif data.startswith("approve_"):
        if user_id != ADMIN_ID: return
        target_id = data.split("_")[1]
        grant_access(target_id)
        await query.message.edit_text(f"✅ **User {target_id} Approved.**")
        await client.send_message(int(target_id), "🎉 **Access Granted!**\nType /start to use the bot.")
    
    elif data.startswith("deny_"):
        if user_id != ADMIN_ID: return
        target_id = data.split("_")[1]
        await query.message.edit_text(f"❌ **User {target_id} Denied.**")
        await client.send_message(int(target_id), "🚫 **Access Denied.**")

    elif data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.answer("❌ You are not the Owner!", show_alert=True)
            return
        users = get_authorized_users()
        if not users:
            await query.answer("No users to remove!", show_alert=True)
            return
        btns = []
        for u in users:
            try: u_info = await client.get_users(int(u)); u_name = u_info.first_name
            except: u_name = "User"
            btns.append([InlineKeyboardButton(f"❌ Remove: {u_name} ({u})", callback_data=f"revoke_{u}")])
        btns.append([InlineKeyboardButton("🔙 Back", callback_data="back_start")])
        await query.message.edit_text("🛡️ **Admin Panel**\nTap to Revoke Access:", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("revoke_"):
        if user_id != ADMIN_ID: return
        target = data.split("_")[1]
        revoke_access(target)
        await query.answer(f"User {target} Removed!")
        users = get_authorized_users()
        if not users:
            await query.message.edit_text("✅ **All users removed.**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]))
        else:
            btns = []
            for u in users:
                try: u_info = await client.get_users(int(u)); u_name = u_info.first_name
                except: u_name = "User"
                btns.append([InlineKeyboardButton(f"❌ Remove: {u_name} ({u})", callback_data=f"revoke_{u}")])
            btns.append([InlineKeyboardButton("🔙 Back", callback_data="back_start")])
            await query.message.edit_reply_markup(InlineKeyboardMarkup(btns))

    elif data == "start_menu" or data == "back_start":
        if not check_access(user_id): return
        font_count = len([f for f in os.listdir(user_dir) if f.endswith(('.ttf', '.otf'))])
        text = (f"**AD Muxing Bot** 🛡️\n\n👋 **Hello, {first_name}**\n\n🔹 **Status:** Operational\n🔹 **Fonts:** {font_count} Saved\n\n🚀 **Ready to Mux**\nSend a **Video File** or **Link** to begin.")
        await query.message.edit_text(text, reply_markup=get_start_kb(user_id))

    elif data == "manage_fonts":
        fonts = [f for f in os.listdir(user_dir) if f.endswith(('.ttf', '.otf'))]
        btns = [[InlineKeyboardButton(f"🗑 {f}", callback_data=f"del_{f}")] for f in fonts]
        btns.append([InlineKeyboardButton("🔙 Back", callback_data="back_start")])
        await query.message.edit_text("📂 **Your Saved Fonts:**\nTap to delete.", reply_markup=InlineKeyboardMarkup(btns))
    
    elif data.startswith("del_"):
        fname = data.split("del_")[1]
        p = os.path.join(user_dir, fname)
        if os.path.exists(p): os.remove(p)
        await query.answer("Deleted")
        await callbacks(client, query)

    elif data == "use_saved_fonts":
        # Start with empty selection so user chooses manually
        user_data[user_id]["fonts"] = []
        await show_font_selection(client, query.message, user_id)
    
    elif data == "upload_new_font":
        user_data[user_id]["step"] = STEP_FONT_DECISION
        await query.message.edit_text("🆗 **Send the .ttf/.otf file now.**")
        
    elif data == "skip_fonts":
        user_data[user_id]["step"] = STEP_SUBTITLE
        await query.message.edit_text("⏩ Fonts Skipped.\n\n📂 **Now send the Subtitle (.ass)**")

    elif data.startswith("toggle_"):
        font = data.split("toggle_")[1]
        selected = user_data[user_id].get("fonts", [])
        if font in selected: selected.remove(font)
        else: selected.append(font)
        user_data[user_id]["fonts"] = selected
        await show_font_selection(client, query.message, user_id)

    elif data == "fonts_selected_done":
        user_data[user_id]["step"] = STEP_SUBTITLE
        count = len(user_data[user_id].get("fonts", []))
        await query.message.edit_text(f"✅ **{count} Fonts Attached.**\n\n📂 **Now send the Subtitle (.ass)**")
    
    elif data == "help_menu":
        msg = ("📚 **Guide:**\n\n1. Send Video/Link\n\n2. Choose/Upload Fonts\n\n3. Send Subtitle (.ass)\n\n4. Enter Name")
        await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]))

# --- INPUT HANDLER ---
@app.on_message(filters.document | filters.video | filters.text)
async def main_handler(client, message):
    user_id = message.from_user.id
    if not check_access(user_id): return
    if user_id not in user_data: 
        user_data[user_id] = {"step": STEP_VIDEO, "fonts": []}

    step = user_data[user_id]["step"]
    user_dir = get_user_font_dir(user_id)
    
    if step == STEP_VIDEO:
        if message.text and message.text.startswith(("http", "https", "magnet")):
            user_data[user_id].update({"video": message.text.strip(), "is_url": True})
            await ask_font_decision(client, message, user_id)
        
        elif message.video or message.document:
            msg = await message.reply_text("⬇️ **Downloading Video...**")
            path = await client.download_media(message, file_name=DOWNLOADS_DIR + "/", progress=progress, progress_args=(msg, time.time()))
            await msg.delete()
            user_data[user_id].update({"video": path, "is_url": False})
            await ask_font_decision(client, message, user_id)

    elif step == STEP_FONT_DECISION:
        file = message.document
        if file and file.file_name.endswith((".ttf", ".otf")):
            msg = await message.reply_text("⬇️ **Saving Font...**")
            path = await client.download_media(message, file_name=f"{user_dir}/{file.file_name}")
            await msg.delete()
            # Auto-select ONLY the new uploaded font
            current_fonts = user_data[user_id].get("fonts", [])
            current_fonts.append(file.file_name)
            user_data[user_id]["fonts"] = current_fonts
            
            await message.reply_text(f"✅ **Saved:** `{file.file_name}`", quote=True)
            await show_font_selection(client, message, user_id)
        
        elif file and file.file_name.endswith(".ass"):
            msg = await message.reply_text("⬇️ **Saving Subtitle...**")
            path = await client.download_media(message, file_name=DOWNLOADS_DIR + "/")
            await msg.delete()
            user_data[user_id]["sub"] = path
            user_data[user_id]["step"] = STEP_NAME
            await message.reply_text("✅ **Subtitle Saved!**\n\n📝 **Final Step:** Enter Output Filename.")
        else:
            await message.reply_text("❌ Send a **Font (.ttf)** or **Subtitle (.ass)**.")

    elif step == STEP_SUBTITLE:
        if message.document and message.document.file_name.endswith(".ass"):
            msg = await message.reply_text("⬇️ **Saving Subtitle...**")
            path = await client.download_media(message, file_name=DOWNLOADS_DIR + "/")
            await msg.delete()
            user_data[user_id]["sub"] = path
            user_data[user_id]["step"] = STEP_NAME
            await message.reply_text("✅ **Subtitle Saved!**\n\n📝 **Final Step:** Enter Output Filename (e.g. `Ep 01`).")
        else: await message.reply_text("❌ Send a valid **.ass** file.")

    elif step == STEP_NAME:
        if not message.text: return
        fname = message.text.strip()
        if not fname.endswith(".mkv"): fname += ".mkv"
        out_path = os.path.join(DOWNLOADS_DIR, fname)
        
        await message.reply_text("⚡ **Muxing Started...**")
        data = user_data[user_id]
        cmd = [FFMPEG_CMD, "-y"]
        
        # INPUT 1: VIDEO
        if data["is_url"]: cmd.extend(["-headers", f"Referer: {data['video']}", "-user_agent", "Mozilla/5.0", "-tls_verify", "0", "-i", data['video']])
        else: cmd.extend(["-i", data['video']])
        
        # INPUT 2: SUBTITLE
        cmd.extend(["-i", data['sub']])
        
        # ATTACH FONTS
        for f in data["fonts"]:
            p = os.path.join(user_dir, f)
            cmd.extend(["-attach", p, "-metadata:s:t", "mimetype=application/x-truetype-font"])
            
        # FORCE DEFAULT SUBTITLE
        cmd.extend(["-map", "0:V", "-map", "0:a", "-map", "1", "-c", "copy", "-disposition:s:0", "default", out_path])
        
        try:
            subprocess.run(cmd, check=True)
            up_msg = await message.reply_text("⬆️ **Uploading...**")
            await client.send_document(user_id, out_path, caption=f"✅ **{fname}**", progress=progress, progress_args=(up_msg, time.time()))
            await up_msg.delete()
            await message.reply_text(f"**Mission Completed !! 👽**")
            
            user_data[user_id] = {"step": STEP_VIDEO, "fonts": []}
            if not data["is_url"] and os.path.exists(data["video"]): os.remove(data["video"])
            os.remove(data["sub"])
        except Exception as e: await message.reply_text(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🤖 Bot Starting...")
    loop = asyncio.get_event_loop()
    loop.create_task(web_server())
    app.run()