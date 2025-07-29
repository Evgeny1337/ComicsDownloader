
import logging
import os
import random
import telegram
from dotenv import load_dotenv
from telegram.ext import Updater, CallbackContext
from bot_helper import get_comic, download_image
from io import BytesIO


logger = logging.getLogger(__name__)

COMIC_BASE_URL = 'https://xkcd.com'
INTERVAL_SECONDS = 3 


def get_random_comic():
    total_comics = get_comic(f'{COMIC_BASE_URL}/info.0.json')['num']
    random_number = random.randint(1, total_comics)
    comic_info = get_comic(f'{COMIC_BASE_URL}/{random_number}/info.0.json')
    return comic_info



def send_comic(bot: telegram.Bot, chat_id: str) -> None:
    try:
        comic_info = get_random_comic()
        image_details = download_image(comic_info)
    except Exception as e:
        bot.send_message(
            chat_id=chat_id,
            text="Не удалось получить комикс."
        )
        return

    img_name = image_details['img_name']
    img_bytes = image_details['img_content']
    caption = image_details['img_alt']

    bot.send_photo(
            chat_id=chat_id,
            photo=BytesIO(img_bytes),
            caption=caption,
            filename=img_name
        )


def send_comic_periodically(context: CallbackContext):
    chat_id = context.bot_data.get('tg_chat_id')
    try:
        context.bot.get_chat(chat_id)
        send_comic(context.bot, chat_id)
    except:
        logger.fatal('Ошибка отправки комикса')


def main():
    load_dotenv(override=True)
    tg_token = os.environ['TG_TOKEN']
    tg_chat_id = os.environ['TG_CHAT_ID']
    updater = Updater(token=tg_token, use_context=True)
    dp = updater.dispatcher
    dp.bot_data['tg_chat_id'] = tg_chat_id

    job_queue = updater.job_queue
    job_queue.run_repeating(
        callback=send_comic_periodically,
        interval=INTERVAL_SECONDS,
        first=0,
        context={'tg_chat_id':tg_chat_id}
    )
    while True:
        updater.start_polling()





if __name__ == '__main__':
    main()