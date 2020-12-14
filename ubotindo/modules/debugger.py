import os
import datetime
from telegram.ext import CommandHandler
from telethon import events
from telegram import Update

from ubotindo import dispatcher, client
from ubotindo.modules.helper_funcs.filters import CustomFilters
from ubotindo.modules.helper_funcs.alternate import typing_action

DEBUG_MODE = False


@typing_action
def debug(update, context):
    global DEBUG_MODE
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    print(DEBUG_MODE)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            DEBUG_MODE = True
            message.reply_text("Debug mode is now on.")
        elif args[1] in ("no", "off"):
            DEBUG_MODE = False
            message.reply_text("Debug mode is now off.")
    else:
        if DEBUG_MODE:
            message.reply_text("Debug mode is currently on.")
        else:
            message.reply_text("Debug mode is currently off.")


@client.on(events.NewMessage(pattern="[/!].*"))
async def i_do_nothing_yes(event):
    global DEBUG_MODE
    if DEBUG_MODE:
        print(f"-{event.from_id} ({event.chat_id}) : {event.text}")
        if os.path.exists("updates.txt"):
            with open("updates.txt", "r") as f:
                text = f.read()
            with open("updates.txt", "w+") as f:
                f.write(
                    text + f"\n-{event.from_id} ({event.chat_id}) : {event.text}")
        else:
            with open("updates.txt", "w+") as f:
                f.write(
                    f"- {event.from_id} ({event.chat_id}) : {event.text} | {datetime.datetime.now()}"
                )


@typing_action
def logs(update, context):
    user = update.effective_user
    with open("ubotindo-log.txt", "rb") as f:
        context.bot.send_document(
            document=f,
            filename=f.name,
            chat_id=user.id,
            caption="This logs that I saved",
        )
        update.effective_message.reply_text("I am send log to your pm 💌")


LOG_HANDLER = CommandHandler(
    "logs", logs, filters=CustomFilters.dev_filter, run_async=True
)
dispatcher.add_handler(LOG_HANDLER)

DEBUG_HANDLER = CommandHandler(
    "debug", debug, filters=CustomFilters.dev_filter, run_async=True
)
dispatcher.add_handler(DEBUG_HANDLER)


__mod_name__ = "Debug"
__command_list__ = ["debug"]
__handlers__ = [DEBUG_HANDLER]
