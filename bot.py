
import os
import zipfile
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from moviepy.editor import ImageSequenceClip
from PIL import Image

BOT_TOKEN = "7508344212:AAHET4lnTAHwsflWeT4ou4i9Via5AiVTNh0"  # ← توکن رباتت اینجا بذار
BOT_NAME = "ربات ویدیو ساز PNG به WebM"
DEFAULT_DURATION = 1.0  # ← مدت زمان پیش‌فرض هر فریم (ثانیه)

user_settings = {}

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    if text.startswith("duration:"):
        try:
            duration = float(text.split(":")[1])
            user_settings[chat_id] = duration
            await update.message.reply_text(f"{BOT_NAME}:\nمدت زمان هر فریم روی {duration} ثانیه تنظیم شد.")
        except ValueError:
            await update.message.reply_text(f"{BOT_NAME}:\nفرمت اشتباهه. مثلا اینجوری بفرست: duration:1.5")

async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    file = update.message.document if update.message.document else update.message.photo[-1]

    os.makedirs("images", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)

    file_path = f"downloads/{file.file_name if hasattr(file, 'file_name') else 'image.png'}"
    await context.bot.get_file(file.file_id).download_to_drive(file_path)

    image_paths = []

    if file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall("images")
        for name in sorted(os.listdir("images")):
            if name.lower().endswith(".png"):
                image_paths.append(os.path.join("images", name))
    else:
        image = Image.open(file_path).convert("RGB")
        img_save = f"images/img_{len(os.listdir('images')):03}.png"
        image.save(img_save)
        image_paths.append(img_save)

    if len(image_paths) < 2:
        await update.message.reply_text(f"{BOT_NAME}:\nلطفاً حداقل دو تصویر PNG بفرست.")
        return

    duration = user_settings.get(chat_id, DEFAULT_DURATION)
    fps = 1 / duration

    clip = ImageSequenceClip(image_paths, fps=fps)
    output_path = "output.webm"
    clip.write_videofile(output_path, codec='libvpx-vp9')

    await update.message.reply_video(video=open(output_path, 'rb'), caption=f"{BOT_NAME}:\nویدیوی شما آماده‌ست!")

    # پاکسازی
    for f in image_paths:
        os.remove(f)
    os.remove(file_path)
    os.remove(output_path)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.Document.IMAGE | filters.PHOTO | filters.Document.ZIP, handle_files))
    app.run_polling()