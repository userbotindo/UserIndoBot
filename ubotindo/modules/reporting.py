# UserindoBot
# Copyright (C) 2020  UserindoBot Team, <https://github.com/userbotindo/UserIndoBot.git>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import html
from typing import Optional

from telegram import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    User,
)
from telegram.error import BadRequest, Unauthorized
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.utils.helpers import mention_html

from ubotindo import LOGGER, dispatcher
from ubotindo.modules.helper_funcs.alternate import typing_action
from ubotindo.modules.helper_funcs.chat_status import (
    user_admin,
    user_not_admin,
)
from ubotindo.modules.log_channel import loggable
from ubotindo.modules.no_sql import get_collection

REPORT_GROUP = 5

USER_REPORT_SETTINGS = get_collection("USER_REPORT_SETTINGS")
CHAT_REPORT_SETTINGS = get_collection("CHAT_REPORT_SETTINGS")


@user_admin
@typing_action
def report_setting(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on", "true"):
                USER_REPORT_SETTINGS.update_one(
                    {'user_id': int(chat.id)},
                    {"$set": {'should_report': True}},
                    upsert=True)
                msg.reply_text(
                    "Turned on reporting! You'll be notified whenever anyone reports something."
                )

            elif args[0] in ("no", "off", "false"):
                USER_REPORT_SETTINGS.update_one(
                    {'user_id': int(chat.id)},
                    {"$set": {'should_report': False}},
                    upsert=True)
                msg.reply_text(
                    "Turned off reporting! You wont get any reports."
                )
        else:
            msg.reply_text(
                "Your current report preference is: `{}`".format(
                    user_should_report(chat.id)
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on", "true"):
                CHAT_REPORT_SETTINGS.update_one(
                    {'chat_id': int(chat.id)},
                    {"$set": {'should_report': True}},
                    upsert=True)
                msg.reply_text(
                    "Turned on reporting! Admins who have turned on reports will be notified when /report "
                    "or @admin are called."
                )

            elif args[0] in ("no", "off", "false"):
                CHAT_REPORT_SETTINGS.update_one(
                    {'chat_id': int(chat.id)},
                    {"$set": {'should_report': False}},
                    upsert=True)
                msg.reply_text(
                    "Turned off reporting! No admins will be notified on /report or @admin."
                )
        else:
            msg.reply_text(
                "This chat's current setting is: `{}`".format(
                    chat_should_report(chat.id)
                ),
                parse_mode=ParseMode.MARKDOWN,
            )


@user_not_admin
@loggable
@typing_action
def report(update, context) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if chat and message.reply_to_message and chat_should_report(chat.id):
        # type: Optional[User]
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()

        isadmeme = chat.get_member(reported_user.id).status
        if isadmeme == "administrator" or isadmeme == "creator":
            return ""  # No point of reporting admins!

        if user.id == reported_user.id:
            message.reply_text("Why the hell you're reporting yourself?")
            return ""

        if reported_user.id == context.bot.id:
            message.reply_text("I'm not gonna report myself!")
            return ""

        if chat.username and chat.type == Chat.SUPERGROUP:

            reported = f"Reported {mention_html(reported_user.id, reported_user.first_name)} to the admins!"

            msg = (
                f"<b>Report from: </b>{html.escape(chat.title)}\n"
                f"<b> × Report by:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
                f"<b> × Reported user:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
            )
            link = f'<b> × Reported message:</b> <a href="https://t.me/{chat.username}/{message.reply_to_message.message_id}">click here</a>'
            should_forward = False
            keyboard = [
                [
                    InlineKeyboardButton(
                        "💬 Message",
                        url=f"https://t.me/{chat.username}/{message.reply_to_message.message_id}",
                    ),
                    InlineKeyboardButton(
                        "⚽ Kick",
                        callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "⛔️ Ban",
                        callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}",
                    ),
                    InlineKeyboardButton(
                        "❎ Delete Message",
                        callback_data=f"report_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}",
                    ),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reported = f"Reported {mention_html(reported_user.id, reported_user.first_name)} to the admins!"

            msg = f'{mention_html(user.id, user.first_name)} is calling for admins in "{html.escape(chat_name)}"!'
            link = ""
            should_forward = True
            keyboard = [
                InlineKeyboardButton(
                    "⚽ Kick",
                    callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}",
                ),
                InlineKeyboardButton(
                    "⛔️ Ban",
                    callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}",
                ),
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if user_should_report(admin.user.id):
                try:
                    context.bot.send_message(
                        admin.user.id,
                        msg + link,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML,
                    )
                    if should_forward:
                        message.reply_to_message.forward(admin.user.id)

                        if (
                            len(message.text.split()) > 1
                        ):  # If user is giving a reason, send his message too
                            message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    if excp.message == "Message_id_invalid":
                        pass
                    else:
                        LOGGER.exception(
                            "Exception while reporting user " + excp.message
                        )

        message.reply_to_message.reply_text(
            reported, parse_mode=ParseMode.HTML
        )
        return msg
    else:
        message.reply_text("Hey... What should i report!")
        return ""


def report_buttons(update, context):
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    if splitter[1] == "kick":
        try:
            context.bot.kickChatMember(splitter[0], splitter[2])
            context.bot.unbanChatMember(splitter[0], splitter[2])
            query.answer("User has been succesfully kicked")
            return ""
        except Exception as err:
            query.answer("⚠️ Failed to kick!")
            context.bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
    elif splitter[1] == "banned":
        try:
            context.bot.kickChatMember(splitter[0], splitter[2])
            query.answer("User has been succesfully banned")
            return ""
        except Exception as err:
            context.bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            query.answer("⚠️ Failed to Ban")
    elif splitter[1] == "delete":
        try:
            context.bot.deleteMessage(splitter[0], splitter[3])
            query.answer("Message has been deleted!")
            return ""
        except Exception as err:
            context.bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            query.answer("⚠️ Failed to delete message!")


def user_should_report(user_id: int) -> bool:
    setting = USER_REPORT_SETTINGS.find_one({'user_id': user_id})
    if not setting:
        return True
    return setting["should_report"]


def chat_should_report(chat_id: int) -> bool:
    setting = CHAT_REPORT_SETTINGS.find_one({'chat_id': chat_id})
    if not setting:
        return True
    return setting["should_report"]


def __migrate__(old_chat_id, new_chat_id):
    CHAT_REPORT_SETTINGS.update_many(
        {'chat_id': old_chat_id},
        {"$set": {'chat_id': new_chat_id}}
    )


def __chat_settings__(chat_id, user_id):
    return "This chat is setup to send user reports to admins, via /report and @admin: `{}`".format(
        chat_should_report(chat_id)
    )


def __user_settings__(user_id):
    return "You receive reports from chats you're admin in: `{}`.\nToggle this with /reports in PM.".format(
        user_should_report(user_id)
    )


__mod_name__ = "Reporting"

__help__ = """
We're all busy people who don't have time to monitor our groups 24/7. But how do you \
react if someone in your group is spamming?

Presenting reports; if someone in your group thinks someone needs reporting, they now have \
an easy way to call all admins.

*Admin only:*
 × /reports <on/off>: Change report setting, or view current status.
   • If done in pm, toggles your status.
   • If in chat, toggles that chat's status.

To report a user, simply reply to user's message with @admin or /report. \
This message tags all the chat admins; same as if they had been @'ed.
You MUST reply to a message to report a user; you can't just use @admin to tag admins for no reason!

Note that the report commands do not work when admins use them; or when used to report an admin. Bot assumes that \
admins don't need to report, or be reported!
"""
REPORT_HANDLER = CommandHandler(
    "report", report, filters=Filters.chat_type.groups, run_async=True
)
SETTING_HANDLER = CommandHandler(
    "reports", report_setting, pass_args=True, run_async=True
)
ADMIN_REPORT_HANDLER = MessageHandler(
    Filters.regex("(?i)@admin(s)?"), report, run_async=True
)
REPORT_BUTTON_HANDLER = CallbackQueryHandler(
    report_buttons, pattern=r"report_"
)

dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(REPORT_BUTTON_HANDLER)
