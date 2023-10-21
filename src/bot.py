from __future__ import annotations
import io
import logging
import os
from typing import Union, BinaryIO

from PIL import Image, ImageDraw, ImageSequence, ImageFont
from telegram import (
    Bot,
    Update,
    Message,
    InlineQueryResultCachedGif,
)
from telegram.ext import (
    Application,
    CommandHandler,
    InlineQueryHandler,
)
from telegram.constants import ParseMode

from src.image_utils import text_wrap

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

BOT_USERNAME = os.environ.get("BOT_USERNAME")
STORAGE_CHAT_ID = os.environ.get("STORAGE_CHAT_ID")

MONKEY_IMAGE_PATH = "src/statics/monkey.gif"
FONT_PATH = "src/statics/font.ttf"


async def start(update: Update, context: dict) -> None:
    text = (
        "Send `/monkey {text}` to get a custom monkey gif. \n"
        "You can also use me as an inline bot in any chat "
        f"by typing `@{BOT_USERNAME} text`"
    )
    await update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN)
    await send_monkey(context.application.bot, update.effective_chat.id, text="AAAAAA")


async def monkey(update: Update, context: dict) -> None:
    text = (update.effective_message.text.split(None, 1)[1:] or [None])[0]
    text = text.upper() if text else None
    await send_monkey(context.application.bot, update.effective_chat.id, text)


async def inline_monkey(update, context):
    query = update.inline_query.query

    if not query:
        return

    results = list()
    message = await send_monkey(context.application.bot, STORAGE_CHAT_ID, query.upper())
    results.append(
        InlineQueryResultCachedGif(
            id=query.upper(),
            gif_file_id=message.animation.file_id,
        )
    )
    await context.bot.answer_inline_query(update.inline_query.id, results)


async def send_monkey(bot: Bot, chat_id: int, text: Union[str, None] = None) -> Message:
    if text:
        monkey_image = get_monkey_text_bytes(text)
    else:
        monkey_image = open(MONKEY_IMAGE_PATH, "rb")

    return await bot.send_animation(chat_id, animation=monkey_image)


def get_monkey_text_bytes(text) -> io.BytesIO | BinaryIO:
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
                (((image.size[0] - w) / 2), y),
                line,
                font=font,
                fill=(255, 255, 255),
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
    token = str(os.environ["TELEGRAM_TOKEN"])

    application = Application.builder().token(token).build()

    # commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monkey", monkey))

    inline_caps_handler = InlineQueryHandler(inline_monkey)
    application.add_handler(inline_caps_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
