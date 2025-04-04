from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from os import environ, path
import random
import logging
from bot_helper import get_comic, download_image
import os
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )


async def get_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    max_photo_size = 20 * 1024 * 1024
    total_comics = get_comic('https://xkcd.com/info.0.json')['num']
    random_number = random.randrange(0, total_comics)
    comic_data = get_comic(f'https://xkcd.com/{random_number}/info.0.json')
    send_data = download_image(comic_data)
    img_name = send_data['img_name']
    img_description = send_data['img_alt']
    if path.isfile(img_name) and path.getsize(img_name) > 0 and path.getsize(img_name) <= max_photo_size:
        with open(img_name, 'rb') as image:
            await update.message.reply_photo(photo=image, caption=img_description, filename=img_name)
        os.remove(img_name)


def main():
    load_dotenv()
    tg_token = environ['TELEGRAM_TOKEN']
    application = Application.builder().token(tg_token).build()
    application.add_handler(CommandHandler('get', get_picture))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()