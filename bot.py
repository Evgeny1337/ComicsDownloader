from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from os import environ, path
import random
from bot_helper import get_comic, download_image
import os
from tempfile import NamedTemporaryFile
import logging

logger = logging.getLogger(__file__)

async def get_random_comic():
    total_comics = get_comic('https://xkcd.com/info.0.json')['num']
    random_number = random.randrange(0, total_comics)
    comic_data = get_comic(f'https://xkcd.com/{random_number}/info.0.json')
    image_data = download_image(comic_data)
    return image_data

async def send_comic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    max_photo_size = 20 * 1024 * 1024
    image_data = await get_random_comic()
    img_name = image_data['img_name']
    img_content = image_data['img_content']
    img_description = image_data['img_alt']
    img_size = len(img_content)
    if img_size == 0 or img_size > max_photo_size:
        await update.message.reply_text(f"Недопустимый размер изображения: {img_size} байт")
        return
    
    with NamedTemporaryFile(suffix=".png", delete=True) as tmp_file:
        tmp_file.write(img_content)
        tmp_file.flush()
        tmp_file.seek(0)

        await update.message.reply_photo(
            photo=tmp_file,
            caption=img_description,
            filename=os.path.basename(img_name)
        )
    

def main():
    load_dotenv()
    tg_token = environ['TG_TOKEN']
    application = Application.builder().token(tg_token).build()
    application.add_handler(CommandHandler('get', send_comic))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)
    main()