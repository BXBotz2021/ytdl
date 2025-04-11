import os
from pyrogram import Client, filters
from pytube import YouTube
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Telegram API details
app = Client(
    "youtube_downloader_bot",
    api_id=7813390,  # 🔁 Replace with your real API ID
    api_hash="1faadd9cc60374bca1e88c2f44e3ee2f",  # 🔁 Replace with your API hash
    bot_token="7782061742:AAGk4KcgzWnuT6sCJEoiCAyn1qAkCqiRkQc"  # 🔁 Replace with your Bot Token
)

# Create downloads directory
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Temporarily store user video data
user_requests = {}

# Start command
@app.on_message(filters.command("start"))
def start(client, message):
    message.reply_text("Yo! 👋 Send me a YouTube link and I'll let you pick the quality.")

# Handle YouTube links
@app.on_message(filters.text & ~filters.command(["start"]))
def handle_youtube_link(client, message):
    url = message.text.strip()

    try:
        yt = YouTube(url)
        video_title = yt.title.encode('utf-8', 'ignore').decode('utf-8')  # Clean title

        streams = yt.streams.filter(progressive=True, file_extension="mp4")

        buttons = []
        for stream in streams:
            filesize = stream.filesize or 0
            quality = f"{stream.resolution} - {round(filesize / (1024 * 1024), 2)}MB"
            buttons.append([
                InlineKeyboardButton(f"Download {quality}", callback_data=f"download_{stream.itag}")
            ])

        user_requests[message.from_user.id] = yt

        message.reply_text(
            f"Choose quality for:\n<b>{video_title}</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="html"
        )

    except Exception as e:
        message.reply_text(f"❌ Error: {e}")

# Handle download button click
@app.on_callback_query()
def handle_download(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id not in user_requests:
        callback_query.answer("Session expired. Send the link again!")
        return

    yt = user_requests[user_id]
    itag = int(callback_query.data.split("_")[1])
    stream = yt.streams.get_by_itag(itag)
    video_title = yt.title.encode('utf-8', 'ignore').decode('utf-8')[:50]  # Short + clean

    if not stream:
        callback_query.message.reply_text("Stream not found 😔")
        return

    try:
        if stream.filesize and stream.filesize > 50 * 1024 * 1024:
            callback_query.message.reply_text("❌ File too large for Telegram (max 50MB).")
            return

        callback_query.message.reply_text("📥 Downloading... Hold tight!")

        file_path = stream.download(output_path=DOWNLOAD_DIR)
        callback_query.message.reply_video(
            video=file_path,
            caption=f"✅ Done! Here's your video: {video_title}"
        )

        os.remove(file_path)
        del user_requests[user_id]

    except Exception as e:
        callback_query.message.reply_text(f"❌ Error: {e}")

# Run the bot
if __name__ == "__main__":
    print("✅ Bot running!")
    app.run()
