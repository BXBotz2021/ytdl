import os
import re
from pyrogram import Client, filters
from pytube import YouTube
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Initialize the bot with your API credentials
app = Client(
    "quality_selection_youtube_downloader_bot",
    api_id=7813390,  # Replace with your API ID
    api_hash="1faadd9cc60374bca1e88c2f44e3ee2f",  # Replace with your API hash
    bot_token="7782061742:AAGk4KcgzWnuT6sCJEoiCAyn1qAkCqiRkQc"  # Replace with your bot token
)

# Directory to save downloaded files
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Store user requests temporarily
user_requests = {}

# Sanitize filename to remove illegal characters
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# Handle the '/start' command
@app.on_message(filters.command("start"))
def start(client, message):
    message.reply_text(
        "Hello! 👋\nSend me a YouTube video link, and I'll let you choose the quality to download. 🎥"
    )

# Handle YouTube video links
@app.on_message(filters.text)
def handle_youtube_link(client, message):
    if message.text.startswith("/"):
        return  # Ignore other commands

    url = message.text.strip()

    try:
        yt = YouTube(url)
        video_title = yt.title
        streams = yt.streams.filter(progressive=True, file_extension="mp4")

        if not streams:
            message.reply_text("No downloadable video streams found.")
            return

        buttons = []
        for stream in streams:
            size_mb = round(stream.filesize / (1024 * 1024), 2)
            buttons.append([
                InlineKeyboardButton(
                    f"{stream.resolution} - {size_mb}MB",
                    callback_data=f"download_{stream.itag}"
                )
            ])

        user_requests[message.from_user.id] = yt

        message.reply_text(
            f"Choose the quality for *{video_title}*:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )

    except Exception as e:
        message.reply_text(f"❌ Error: {e}")

# Handle quality selection and download
@app.on_callback_query()
def handle_quality_selection(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id not in user_requests:
        callback_query.answer("Session expired. Please send the link again.")
        return

    yt = user_requests[user_id]
    itag = int(callback_query.data.split("_")[1])

    try:
        stream = yt.streams.get_by_itag(itag)
        video_title = yt.title
        clean_title = sanitize_filename(video_title)
        video_path = stream.download(output_path=DOWNLOAD_DIR, filename=clean_title + ".mp4")

        if not os.path.exists(video_path):
            callback_query.message.reply_text("❌ Download failed. File not found.")
            return

        file_size = os.path.getsize(video_path)
        if file_size > 50 * 1024 * 1024:
            callback_query.message.reply_text(
                f"⚠️ File too large for Telegram ({round(file_size / (1024 * 1024), 2)}MB > 50MB)."
            )
            os.remove(video_path)
            return

        callback_query.message.reply_text("✅ Download complete! Sending video...")
        callback_query.message.reply_video(
            video=video_path,
            caption=f"Here is your video: {video_title}"
        )

        os.remove(video_path)
        del user_requests[user_id]

    except Exception as e:
        callback_query.message.reply_text(f"❌ Error during download: {e}")

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()
