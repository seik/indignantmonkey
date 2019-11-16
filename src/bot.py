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
from telegram.ext import Dispatcher, CommandHandler, InlineQueryHandler

from src.image_utils import text_wrap

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps("ok"),
}
ERROR_RESPONSE = {"statusCode": 400, "body": json.dumps("Oops, something went wrong!")}

BOT_USERNAME = os.environ.get("BOT_USERNAME")

STORAGE_CHAT_ID = os.environ.get("STORAGE_CHAT_ID")

MONKEY_IMAGE_PATH = "src/statics/monkey.gif"

FONT_PATH = "src/statics/font.ttf"


def configure_telegram():
    """
    Configures the bot with a Telegram Token.
    Returns a bot instance.
    """

    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    if not telegram_token:
        logger.error("The TELEGRAM_TOKEN must be set")
        raise NotImplementedError

    return Bot(telegram_token)


def set_up_dispatcher(dispatcher: Dispatcher) -> None:
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("monkey", monkey))
    inline_caps_handler = InlineQueryHandler(inline_monkey)
    dispatcher.add_handler(inline_caps_handler)


bot = configure_telegram()
dispatcher = Dispatcher(bot, None, use_context=True)


def handler(event, context) -> dict:
    logger.info(f"Event: {event}")

    try:
        dispatcher.process_update(Update.de_json(json.loads(event.get("body")), bot))
    except Exception as e:
        logger.error(e)
        return ERROR_RESPONSE

    return OK_RESPONSE


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


set_up_dispatcher(dispatcher)
