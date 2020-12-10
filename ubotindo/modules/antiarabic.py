import html
from typing import Optional, List
from telegram import Message, Chat, Update, Bot, User, ParseMode
from telegram.ext import CommandHandler, MessageHandler, run_async, Filters
from telegram.utils.helpers import mention_html
from ubotindo import dispatcher, CallbackContext, LOGGER, SUDO_USERS
from ubotindo.modules.helper_funcs.chat_status import user_not_admin, user_admin, can_delete, is_user_admin, bot_admin
from ubotindo.modules.log_channel import loggable
from ubotindo.modules.helper_funcs.extraction import extract_text
from ubotindo.modules.sql import antiarabic_sql as sql

ANTIARABIC_GROUPS = 12


@user_admin
def antiarabic_setting(update, context):
    bot = context.bot
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    user = update.effective_user
    member = chat.get_member(int(user.id))

    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text(
                    "Turned on AntiArabic! Messages sent by any non-admin which contains arabic text "
                    "will be deleted.")

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text(
                    "Turned off AntiArabic! Messages containing arabic text won't be deleted."
                )
        else:
            msg.reply_text("This chat's current setting is: `{}`".format(
                sql.chat_antiarabic(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)


@bot_admin
@user_not_admin
def antiarabic(update, context):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    to_match = extract_text(msg)
    user = update.effective_user  # type: Optional[User]
    has_arabic = False

    if not sql.chat_antiarabic(chat.id):
        return ""

    if not user.id or int(user.id) == 777000 or int(user.id) == 1087968824:
        return ""

    if not to_match:
        return

    if chat.type != chat.PRIVATE:
        for c in to_match:
            if ('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F'
                    or '\u08A0' <= c <= '\u08FF' or '\uFB50' <= c <= '\uFDFF'
                    or '\uFE70' <= c <= '\uFEFF'
                    or '\U00010E60' <= c <= '\U00010E7F'
                    or '\U0001EE00' <= c <= '\U0001EEFF'):
                if can_delete(chat, bot.id):
                    update.effective_message.delete()
                    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat is setup to delete messages containing Arabic: `{}`".format(
        sql.chat_antiarabic(chat_id))


SETTING_HANDLER = CommandHandler("antiarabic",
                                 antiarabic_setting,
                                 run_async=True)
ANTI_ARABIC = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo)
    & Filters.chat_type.groups,
    antiarabic,
    run_async=True)

dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(ANTI_ARABIC, group=ANTIARABIC_GROUPS)
