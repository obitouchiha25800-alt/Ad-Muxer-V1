from pyrogram import Client

print("--- Login Helper ---")
# Yahan apne credentials daalne ki zaroorat nahi, ye run karne par poochega
api_id = input("Enter Your API ID: ")
api_hash = input("Enter Your API HASH: ")

# Ye 'my_sub_bot' wo naam hai jo session file ka hoga
app = Client("my_sub_bot", api_id=api_id, api_hash=api_hash)

print("\nConnecting to Telegram...")
app.start()
print("\n✅ Login Successful! 'my_sub_bot.session' file ban gayi hai.")
print("Ab is file ko Server par upload kar do.")
app.stop()