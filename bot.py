
import logging
import os
import random
import threading
import telegram
from dotenv import load_dotenv, find_dotenv, set_key
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from bot_helper import get_comic, download_image
from io import BytesIO


logger = logging.getLogger(__name__)


MAX_PHOTO_SIZE = 20 * 1024 * 1024  
INPUT_MANUALLY = 1
COMIC_BASE_URL = 'https://xkcd.com'
INTERVAL_SECONDS = 3600  


active_threads = {} 

class MyLogsHandler(logging.Handler):
    def __init__(self, bot: telegram.Bot, chatid:str = None, level = 0):
        super().__init__(level)
        self.bot = bot
        self.chatid = chatid
        
    def emit(self, record):
        log_entry = self.format(record)
        chat_id = self.chatid
        if chat_id:
            self.bot.send_message(chat_id=chat_id, text=log_entry)

    def set_chatid(self, chatid):
        self.chatid = chatid

def save_chat_id(chat_id: str):
    env_path = find_dotenv()
    set_key(env_path, 'TG_CHAT_ID', chat_id)
    os.environ['TG_CHAT_ID'] = chat_id


def get_main_keyboard():
    keyboard = [
        ['Выбрать данный чат для получения комиксов'],
        ['Ввести вручную id чата для отправки комиксов']
    ]
    return telegram.ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_random_comic():
    total_comics = get_comic(f'{COMIC_BASE_URL}/info.0.json')['num']
    random_number = random.randint(1, total_comics) 
    comic_data = get_comic(f'{COMIC_BASE_URL}/{random_number}/info.0.json')
    return download_image(comic_data)


def create_scheduler(bot: telegram.Bot, chat_id: str):
    stop_previous_thread(chat_id)

    stop_event = threading.Event()
    
    thread = threading.Thread(
        target=send_comic_periodically,
        args=(bot, chat_id, stop_event),
        daemon=True
    )
    thread.start()
    
    active_threads[chat_id] = stop_event
    logger.info(f"Запущен планировщик для чата {chat_id}")


def stop_previous_thread(chat_id: str):
    if chat_id in active_threads:
        active_threads[chat_id].set()
        del active_threads[chat_id]
        logger.info(f"Остановлен предыдущий поток для чата {chat_id}")


def send_comic(bot: telegram.Bot, chat_id: str) -> None:
    try:
        comic_data = get_random_comic()
    except Exception as e:
        logger.error(f"Ошибка при получении комикса: {e}")
        bot.send_message(
            chat_id=chat_id,
            text="Не удалось получить комикс. Попробуйте позже."
        )
        return

    img_name = comic_data['img_name']
    img_bytes = comic_data['img_content']
    caption = comic_data['img_alt']

    if len(img_bytes) > MAX_PHOTO_SIZE:
        bot.send_message(
            chat_id=chat_id,
            text=f"Размер изображения слишком большой: {len(img_bytes) // 1024} KB"
        )
        return
    try:
        bot.send_photo(
            chat_id=chat_id,
            photo=BytesIO(img_bytes),
            caption=caption,
            filename=img_name
        )
    except telegram.error.TelegramError as e:
        logger.error(f"Ошибка отправки: {e}")
        bot.send_message(
            chat_id=chat_id,
            text=f"Ошибка отправки комикса: {str(e)}"
        )


def send_comic_periodically(bot: telegram.Bot, chat_id: str, stop_event: threading.Event):
    while not stop_event.is_set():
        send_comic(bot, chat_id)
        stop_event.wait(timeout=INTERVAL_SECONDS)


def start(update: telegram.Update, context: CallbackContext):
    update.message.reply_text(
        'Бот для отправки случайных XKCD комиксов',
        reply_markup=get_main_keyboard()
    )


def request_manual_input(update: telegram.Update, context: CallbackContext):
    update.message.reply_text(
        "Введите ID чата (группы или канала) для отправки комиксов:"
    )
    return INPUT_MANUALLY


def use_current_chat(update: telegram.Update, context: CallbackContext):
    chat_id = str(update.message.chat.id)
    try:
        context.bot.get_chat(chat_id)
        save_chat_id(chat_id)
        create_scheduler(context.bot, chat_id)
        logger_handler = context.bot_data.get('logger_handler')
        logger_handler.set_chatid(chat_id)
        logger.info(f"Теперь комиксы будут приходить сюда! (ID: {chat_id}")
    except telegram.error.TelegramError as error:
        error_message = f"Ошибка доступа к чату {chat_id}: {error.message}"
        logger.error(error_message)


def handle_manual_input(update: telegram.Update, context: CallbackContext) -> int:
    chat_id = update.message.text.strip()
    
    try:
        context.bot.get_chat(chat_id)
        save_chat_id(chat_id)
        create_scheduler(context.bot, chat_id)
        update.message.reply_text(
            f"Настройки сохранены! Комиксы будут отправляться в чат: {chat_id}",
            reply_markup=get_main_keyboard()
        )
    except telegram.error.TelegramError as e:
        logger.error(f"Невалидный chat_id: {chat_id}, ошибка: {e}")
        update.message.reply_text(
            "Ошибка: Недопустимый ID чата или бот не добавлен в чат",
            reply_markup=get_main_keyboard()
        )
    
    return ConversationHandler.END


def stop_bot(update: telegram.Update, context: CallbackContext):
    chat_id = str(update.message.chat.id)
    stop_previous_thread(chat_id)
    update.message.reply_text("Рассылка комиксов остановлена!")


def main():
    load_dotenv(override=True)
    tg_token = os.getenv('TG_TOKEN')
    logger.setLevel(logging.DEBUG)
    
    if not tg_token:
        logger.critical("Токен бота не найден!")
        return

    tg_chat_id = os.getenv('TG_CHAT_ID', '').strip()
    updater = Updater(token=tg_token, use_context=True)

    logger_handler = MyLogsHandler(bot=updater.bot, chatid=tg_chat_id)
    logger.addHandler(logger_handler)
    
    dp = updater.dispatcher
    dp.bot_data['logger_handler'] = logger_handler
    
    if tg_chat_id:
        create_scheduler(updater.bot, tg_chat_id)

    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('stop', stop_bot))
    
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                Filters.regex(r'^Ввести вручную id чата'),
                request_manual_input
            )
        ],
        states={
            INPUT_MANUALLY: [
                MessageHandler(Filters.text & ~Filters.command, handle_manual_input)
            ]
        },
        fallbacks=[]
    )
    dp.add_handler(conv_handler)
    
    dp.add_handler(MessageHandler(
        Filters.regex(r'^Выбрать данный чат'),
        use_current_chat
    ))

    updater.start_polling()
    logger.info("Бот запущен и работает...")
    updater.idle()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )
    main()