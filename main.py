import logging
from functions import *
from telegram.ext import Application, MessageHandler, filters
from telegram import InlineKeyboardMarkup
from config import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.run_polling()


if __name__ == '__main__':
    main()
