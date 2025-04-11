import os
from pyrogram import Client, filters
from pytube import YouTube
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Initialize the bot with your API credentials
app = Client(
    "ytdl",
    api_id=123456,  # Replace with your API ID from https://my.telegram.org/apps
    api_hash="your_api_hash",  # Replace with your API hash from https://my.telegram.org/apps
    bot_token="your_bot_token"  # Replace with your bot token from @BotFather
)

# Directory to save downloaded files
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Store user requests temporarily
user_requests = {}

# Handle the '/start' command
@app.on_message(filters.command("start"))
def start(client, message):
    message.reply_text(
        "Hello! 👋\nSend me a YouTube video link, and I'll let you choose the quality to download. 🎥"
    )

# Handle YouTube video links
@app.on_message(filters.text & ~filters.command)
def handle_youtube_link(client, message):
    url = message.text.strip()

    try:
        # Initialize YouTube object
        yt = YouTube(url)
        video_title = yt.title

        # Fetch available streams (video only or video+audio)
        streams = yt.streams.filter(progressive=True, file_extension="mp4")

        # Generate InlineKeyboard buttons for available qualities
        buttons = []
        for stream in streams:
            quality = f"{stream.resolution} - {round(stream.filesize / (1024 * 1024), 2)}MB"
            buttons.append(
                [InlineKeyboardButton(f"Download {quality}", callback_data=f"download_{stream.itag}")]
            )

        # Save video object for this user
        user_requests[message.from_user.id] = yt

        # Send quality selection message
        message.reply_text(
            f"Choose the quality for '{video_title}':",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        message.reply_text(f"An error occurred: {e}")

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
        # Get the selected stream
        stream = yt.streams.get_by_itag(itag)
        video_title = yt.title

        # Check file size limit (50MB for Telegram bots)
        if stream.filesize > 50 * 1024 * 1024:
            callback_query.message.reply_text(
                "The selected file is too large to be sent via Telegram (limit: 50MB)."
            )
            return

        # Notify user and download the video
        callback_query.message.reply_text(f"Downloading '{video_title}'... Please wait.")
        video_path = stream.download(output_path=DOWNLOAD_DIR)

        # Send the downloaded video to the user
        callback_query.message.reply_video(
            video=video_path, caption=f"Here is your video: {video_title}"
        )

        # Cleanup
        os.remove(video_path)
        del user_requests[user_id]  # Clear user request after processing
    except Exception as e:
        callback_query.message.reply_text(f"An error occurred: {e}")

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()
