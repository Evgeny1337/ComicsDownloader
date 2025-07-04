
import logging
import os
import random
import threading
import telegram
from dotenv import load_dotenv, find_dotenv, set_key
from telegram.ext import Updater, CommandHandler, CallbackContext
import telegram.ext
from bot_helper import get_comic, download_image
from io import BytesIO

logger = logging.getLogger(__name__)

class LogsHandler(logging.Handler):

    def __init__(self,chat_id:str, bot: telegram.ext.ExtBot, level = 0):
        super().__init__(level)
        format = logging.Formatter("%(process)d %(levelname)s %(message)s")
        self.setFormatter(format)
        self.bot = bot
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        if self.chat_id:
            self.bot.send_message(chat_id=self.chat_id, text=log_entry)

    def set_chatid(self,chat_id):
        self.chat_id = chat_id


COMIC_BASE_URL = 'https://xkcd.com'
INTERVAL_SECONDS = 3600  


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
        logger.error(f"Ошибка при получении комикса: {e}")
        bot.send_message(
            chat_id=chat_id,
            text="Не удалось получить комикс. Попробуйте позже."
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
    if chat_id:
        try:
            context.bot.get_chat(chat_id)
            send_comic(context.bot, chat_id)
        except telegram.error.TelegramError as err:
            logger.warning('В чат с id {} не возможно отправить сообщение\n\n {}'.format(chat_id,err))



def start(update: telegram.Update, context: CallbackContext):
    chat_id = update.message.chat_id
    current_chat_id = context.bot_data.get('tg_chat_id')
    update.message.reply_text("Бот для отправки комиксов, id вашего чата {}".format(chat_id))
    if not current_chat_id:
         update.message.reply_text("id чата для отправки комиксов не задан")




def main():
    load_dotenv(override=True)
    tg_token = os.getenv('TG_TOKEN')
    tg_chat_id = os.getenv('TG_CHAT_ID', '').strip()
    updater = Updater(token=tg_token, use_context=True)

    dp = updater.dispatcher
    dp.bot_data['tg_chat_id'] = tg_chat_id
    dp.add_handler(CommandHandler('start', start))
    logging_bot = telegram.Bot(token=tg_token)

    logger.addHandler(LogsHandler(tg_chat_id,logging_bot))
    logger.setLevel(logging.INFO)
    logger.info('Рассылка запущена')

    job_queue = updater.job_queue
    job_queue.run_repeating(
        callback=send_comic_periodically,
        interval=INTERVAL_SECONDS,
        first=0,
        context={'tg_chat_id':tg_chat_id}
    )
    try:
        while True:
            updater.start_polling()
    except Exception:
        logger.warning('Рассылка приостановллена')





if __name__ == '__main__':
    main()