import io
import json
import logging
import os
from typing import Union, BinaryIO

from PIL import Image, ImageDraw, ImageSequence, ImageFont
from telegram import (
    Update,
    Bot,
    Message,
    InlineQueryResultCachedGif,
    ParseMode,
)
from telegram.ext import Updater, Dispatcher, CommandHandler, InlineQueryHandler

from src.image_utils import text_wrap

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

BOT_USERNAME = os.environ.get("BOT_USERNAME")

STORAGE_CHAT_ID = os.environ.get("STORAGE_CHAT_ID")

MONKEY_IMAGE_PATH = "src/statics/monkey.gif"

FONT_PATH = "src/statics/font.ttf"


def start(update: Update, context: dict) -> None:
    text = (
        "Send `/monkey {text}` to get a custom monkey gif. \n"
        "You can also use me as an inline bot in any chat "
        f"by typing `@{BOT_USERNAME} text`"
    )

    bot.send_message(
        chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN
    )
    send_monkey(update.effective_chat.id, text="AAAAAA")


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def monkey(update: Update, context: dict) -> None:
    text = (update.effective_message.text.split(None, 1)[1:] or [None])[0]
    text = text.upper() if text else None
    send_monkey(update.effective_chat.id, text)


def inline_monkey(update, context):
    query = update.inline_query.query

    if not query:
        return

    results = list()
    message = send_monkey(STORAGE_CHAT_ID, query.upper())
    results.append(
        InlineQueryResultCachedGif(
            id=query.upper(), gif_file_id=message.animation.file_id,
        )
    )
    context.bot.answer_inline_query(update.inline_query.id, results)


def send_monkey(chat_id: int, text: Union[str, None] = None) -> Message:
    if text:
        monkey_image = get_monkey_text_bytes(text)
    else:
        monkey_image = open(MONKEY_IMAGE_PATH, "rb")

    return bot.send_animation(chat_id=chat_id, animation=monkey_image)


def get_monkey_text_bytes(text) -> Union[io.BytesIO, BinaryIO]:
    image = Image.open(MONKEY_IMAGE_PATH)
    frames = []
    for frame in ImageSequence.Iterator(image):
        frame = frame.convert("RGB")
        image_draw = ImageDraw.Draw(frame)
        font = ImageFont.truetype(FONT_PATH, size=30)

        # Divide lines by text width
        lines = text_wrap(text, font, image.size[0])
        # Get line height with a plus
        line_height = font.getsize("hg")[1] + 5

        # Get the starting y point for the first line
        y = image.size[1] - (line_height * len(lines))

        for line in lines:
            w, _ = image_draw.textsize(line, font=font)
            image_draw.text(
                (((image.size[0] - w) / 2), y), line, font=font, fill=(255, 255, 255),
            )

            # Increase y by line height for the next line
            y = y + line_height

        frames.append(frame)

    monkey_bytes = io.BytesIO()
    monkey_bytes.name = "monkey.gif"

    frames[0].save(
        monkey_bytes,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        transparency=True,
        optimize=False,
    )

    monkey_bytes.seek(0)
    return monkey_bytes


def main():
    token = str(os.environ['TELEGRAM_TOKEN'])

    bot = Bot(token)

    updater = Updater(bot)

    dispatcher = Dispatcher(bot, None, use_context=True)

    # commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("monkey", monkey))
    inline_caps_handler = InlineQueryHandler(inline_monkey)
    dispatcher.add_handler(inline_caps_handler)
    dp.add_handler(CommandHandler("shot", shot))

    updater.start_polling()

    # log all errors
    dp.add_error_handler(error)

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
