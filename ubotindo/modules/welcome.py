# UserindoBot
# Copyright (C) 2020  UserindoBot Team, <https://github.com/MoveAngel/UserIndoBot.git>
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

import re
import time
from html import escape
from functools import partial

from telegram import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.utils.helpers import mention_html, mention_markdown, escape_markdown

import ubotindo.modules.sql.welcome_sql as sql
from ubotindo import (
    DEV_USERS,
    LOGGER,
    MESSAGE_DUMP,
    OWNER_ID,
    dispatcher,
    spamwtc,
)
from ubotindo.modules.helper_funcs.alternate import send_message, typing_action
from ubotindo.modules.helper_funcs.chat_status import (
    is_user_ban_protected,
    user_admin,
)
from ubotindo.modules.helper_funcs.misc import (
    build_keyboard,
    build_keyboard_parser,
    revert_buttons,
)
from ubotindo.modules.helper_funcs.msg_types import get_welcome_type
from ubotindo.modules.helper_funcs.string_handling import (
    escape_invalid_curly_brackets,
    markdown_parser,
    markdown_to_html,
)
from ubotindo.modules.log_channel import loggable
from ubotindo.modules.sql.global_bans_sql import is_user_gbanned

VALID_WELCOME_FORMATTERS = [
    "first",
    "last",
    "fullname",
    "username",
    "id",
    "count",
    "chatname",
    "mention",
]

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
}


VERIFIED_USER_WAITLIST = {}

# do not async
def send(update, message, keyboard, backup_message):
    chat = update.effective_chat
    cleanserv = sql.clean_service(chat.id)
    reply = update.message.message_id
    # Clean service welcome
    if cleanserv:
        try:
            dispatcher.bot.delete_message(chat.id, update.message.message_id)
        except BadRequest:
            pass
        reply = False

    try:
        msg = update.effective_message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            reply_to_message_id=reply,
        )
    except IndexError:
        msg = update.effective_message.reply_text(
            markdown_parser(
                backup_message + "\nNote: the current message was "
                "invalid due to markdown issues. Could be "
                "due to the user's name."
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_to_message_id=reply,
        )
    except KeyError:
        msg = update.effective_message.reply_text(
            markdown_parser(
                backup_message + "\nNote: the current message is "
                "invalid due to an issue with some misplaced "
                "curly brackets. Please update"
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_to_message_id=reply,
        )
    except BadRequest as excp:
        if excp.message == "Have no rights to send a message":
            LOGGER.warn(
                "can't send message on {}! leaving...".format(
                    update.effective_message.chat.id
                )
            )
            dispatcher.bot.leaveChat(update.effective_message.chat.id)
            return
        elif excp.message == "Button_url_invalid":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message + "\nNote: the current message has an invalid url "
                    "in one of its buttons. Please update."
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
        elif excp.message == "Unsupported url protocol":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message + "\nNote: the current message has buttons which "
                    "use url protocols that are unsupported by "
                    "telegram. Please update."
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
        elif excp.message == "Wrong url host":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message + "\nNote: the current message has some bad urls. "
                    "Please update."
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
            LOGGER.warning(message)
            LOGGER.warning(keyboard)
            LOGGER.exception("Could not parse! got invalid url host errors")
        elif excp.message == "Reply message not found":
            msg = dispatcher.bot.send_message(
                chat.id,
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        else:
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message + "\nNote: An error occured when sending the "
                    "custom message. Please update."
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
            LOGGER.exception()

    return msg


@loggable
def new_member(update, context):

    bot, job_queue = context.bot, context.job_queue

    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    should_welc, cust_welcome, cust_content, welc_type = sql.get_welc_pref(chat.id)
    welc_mutes = sql.welcome_mutes(chat.id)
    human_checks = sql.get_human_checks(user.id, chat.id)

    new_members = update.effective_message.new_chat_members
    chat_name = chat.title or chat.first or chat.username

    for new_mem in new_members:

        welcome_log = None
        res = None
        sent = None
        should_mute = True
        welcome_bool = True
        media_wel = False

        if spamwtc != None:
            sw = spamwtc.get_ban(new_mem.id)
            if sw:
                return

        if should_welc:

            reply = update.message.message_id
            cleanserv = sql.clean_service(chat.id)
            # Clean service welcome
            if cleanserv:
                try:
                    dispatcher.bot.delete_message(chat.id, update.message.message_id)
                except BadRequest:
                    pass
                reply = False

            # Give the owner a special welcome
            if new_mem.id == OWNER_ID:
                update.effective_message.reply_text(
                    "My Owner in the house Let's party 🎉", reply_to_message_id=reply
                )
                welcome_log = (
                    f"{escape(chat.title)}\n"
                    f"#USER_JOINED\n"
                    f"Bot Owner just joined the chat"
                )
                continue

            # Welcome Devs
            elif new_mem.id in DEV_USERS:
                update.effective_message.reply_text(
                    "My Dev Here, let's see what happened now 🔥",
                    reply_to_message_id=reply,
                )
                continue

            # Welcome yourself
            elif new_mem.id == context.bot.id:
                try:
                    update.effective_message.reply_text(
                        "Hey 😍 {}, I'm {}! Thank you for adding me to {}".format(
                            user.first_name, context.bot.first_name, chat_name
                        ),
                        reply_to_message_id=reply,
                    )
                except BadRequest as err:
                    if err.message == "Have no rights to send a message":
                        pass

            else:
                buttons = sql.get_welc_buttons(chat.id)
                keyb = build_keyboard(buttons)

                if welc_type not in (sql.Types.TEXT, sql.Types.BUTTON_TEXT):
                    media_wel = True

                first_name = (
                    new_mem.first_name or "PersonWithNoName"
                )  # edge case of empty name - occurs for some bugs.

                if cust_welcome:
                    if cust_welcome == sql.DEFAULT_WELCOME:
                        cust_welcome = sql.DEFAULT_WELCOME.format(first=escape_markdown(first_name))

                    if new_mem.last_name:
                        fullname = escape_markdown(f"{first_name} {new_mem.last_name}")
                    else:
                        fullname = escape_markdown(first_name)
                    count = chat.get_members_count()
                    mention = mention_markdown(new_mem.id, escape_markdown(first_name))
                    if new_mem.username:
                        username = "@" + escape_markdown(new_mem.username)
                    else:
                        username = mention

                    valid_format = escape_invalid_curly_brackets(
                        cust_welcome, VALID_WELCOME_FORMATTERS
                    )
                    res = valid_format.format(
                        first=escape_markdown(first_name),
                        last=escape_markdown(new_mem.last_name or first_name),
                        fullname=escape_markdown(fullname),
                        username=username,
                        mention=mention,
                        count=count,
                        chatname=escape_markdown(chat.title),
                        id=new_mem.id,
                    )

                else:
                    res = sql.DEFAULT_WELCOME.format(
                        first=escape_markdown(first_name)
                    )
                    keyb = []

                backup_message = sql.DEFAULT_WELCOME.format(
                    first=escape_markdown(first_name)
                )
                keyboard = InlineKeyboardMarkup(keyb)

        else:
            welcome_bool = False
            res = None
            keyboard = None
            backup_message = None
            reply = None

        # User exceptions from welcomemutes
        if (
            is_user_ban_protected(chat, new_mem.id, chat.get_member(new_mem.id))
            or human_checks
        ):
            should_mute = False
        # Join welcome: soft mute
        if new_mem.is_bot:
            should_mute = False

        if user.id == new_mem.id:
            if should_mute:
                if welc_mutes == "soft":
                    bot.restrict_chat_member(
                        chat.id,
                        new_mem.id,
                        permissions=ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                            can_send_polls=False,
                            can_change_info=False,
                            can_add_web_page_previews=False,
                        ),
                        until_date=(int(time.time() + 24 * 60 * 60)),
                    )
                if welc_mutes == "strong":
                    welcome_bool = False
                    if not media_wel:
                        VERIFIED_USER_WAITLIST.update(
                            {
                                new_mem.id: {
                                    "should_welc": should_welc,
                                    "media_wel": False,
                                    "status": False,
                                    "update": update,
                                    "res": res,
                                    "keyboard": keyboard,
                                    "backup_message": backup_message,
                                }
                            }
                        )
                    else:
                        VERIFIED_USER_WAITLIST.update(
                            {
                                new_mem.id: {
                                    "should_welc": should_welc,
                                    "chat_id": chat.id,
                                    "status": False,
                                    "media_wel": True,
                                    "cust_content": cust_content,
                                    "welc_type": welc_type,
                                    "res": res,
                                    "keyboard": keyboard,
                                }
                            }
                        )
                    new_join_mem = f"[{escape_markdown(new_mem.first_name)}](tg://user?id={user.id})"
                    message = msg.reply_text(
                        f"{new_join_mem}, click the button below to prove you're human.\nYou have 120 seconds.",
                        reply_markup=InlineKeyboardMarkup(
                            [
                                {
                                    InlineKeyboardButton(
                                        text="Yes, I'm human.",
                                        callback_data=f"user_join_({new_mem.id})",
                                    )
                                }
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_to_message_id=reply,
                    )
                    bot.restrict_chat_member(
                        chat.id,
                        new_mem.id,
                        permissions=ChatPermissions(
                            can_send_messages=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                            can_send_polls=False,
                            can_change_info=False,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_add_web_page_previews=False,
                        ),
                    )
                    job_queue.run_once(
                        partial(check_not_bot, new_mem, chat.id, message.message_id),
                        120,
                        name="welcomemute",
                    )

        if welcome_bool:
            if media_wel:
                if ENUM_FUNC_MAP[welc_type] == dispatcher.bot.send_sticker:
                    sent = ENUM_FUNC_MAP[welc_type](
                        chat.id,
                        cust_content,
                        reply_markup=keyboard,
                        reply_to_message_id=reply,
                    )
                else:
                    sent = ENUM_FUNC_MAP[welc_type](
                        chat.id,
                        cust_content,
                        caption=res,
                        reply_markup=keyboard,
                        reply_to_message_id=reply,
                        parse_mode="markdown",
                    )
            else:
                sent = send(update, res, keyboard, backup_message)
            prev_welc = sql.get_clean_pref(chat.id)
            if prev_welc:
                try:
                    bot.delete_message(chat.id, prev_welc)
                except BadRequest:
                    pass

                if sent:
                    sql.set_clean_welcome(chat.id, sent.message_id)

        if welcome_log:
            return welcome_log

        return (
            f"{escape(chat.title)}\n"
            f"#USER_JOINED\n"
            f"<b>User</b>: {mention_html(user.id, user.first_name)}\n"
            f"<b>ID</b>: <code>{user.id}</code>"
        )

    return ""


def check_not_bot(member, chat_id, message_id, context):
    bot = context.bot
    member_dict = VERIFIED_USER_WAITLIST.pop(member.id)
    member_status = member_dict.get("status")
    if not member_status:
        try:
            bot.unban_chat_member(chat_id, member.id)
        except:
            pass

        try:
            bot.edit_message_text(
                "**This User Not Verify in 120sec**\nKicked Now!!!",
                chat_id=chat_id,
                message_id=message_id,
            )
        except:
            pass


def left_member(update, context):
    chat = update.effective_chat
    should_goodbye, cust_goodbye, goodbye_type = sql.get_gdbye_pref(chat.id)
    cust_goodbye = markdown_to_html(cust_goodbye)
    if should_goodbye:
        reply = update.message.message_id
        cleanserv = sql.clean_service(chat.id)
        # Clean service welcome
        if cleanserv:
            try:
                dispatcher.bot.delete_message(chat.id, update.message.message_id)
            except BadRequest:
                pass
            reply = False

        left_mem = update.effective_message.left_chat_member
        if left_mem:

            # Ignore gbanned users
            if is_user_gbanned(left_mem.id):
                return

            # Ignore spamwatch banned users
            try:
                sw = spamwtc.get_ban(int(left_mem.id))
                if sw:
                    return
            except BaseException:
                pass

            # Ignore bot being kicked
            if left_mem.id == context.bot.id:
                return

            # Give the owner a special goodbye
            if left_mem.id == OWNER_ID:
                update.effective_message.reply_text(
                    "RIP Master", reply_to_message_id=reply
                )
                return

            # if media goodbye, use appropriate function for it
            if goodbye_type != sql.Types.TEXT and goodbye_type != sql.Types.BUTTON_TEXT:
                ENUM_FUNC_MAP[goodbye_type](chat.id, cust_goodbye)
                return

            first_name = (
                left_mem.first_name or "PersonWithNoName"
            )  # edge case of empty name - occurs for some bugs.
            if cust_goodbye:
                if left_mem.last_name:
                    fullname = "{} {}".format(first_name, left_mem.last_name)
                else:
                    fullname = first_name
                count = chat.get_members_count()
                mention = mention_html(left_mem.id, first_name)
                if left_mem.username:
                    username = "@" + escape(left_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(
                    cust_goodbye, VALID_WELCOME_FORMATTERS
                )
                res = valid_format.format(
                    first=escape(first_name),
                    last=escape(left_mem.last_name or first_name),
                    fullname=escape(fullname),
                    username=username,
                    mention=mention,
                    count=count,
                    chatname=escape(chat.title),
                    id=left_mem.id,
                )
                buttons = sql.get_gdbye_buttons(chat.id)
                keyb = build_keyboard(buttons)

            else:
                res = sql.DEFAULT_GOODBYE
                keyb = []

            keyboard = InlineKeyboardMarkup(keyb)

            send(update, res, keyboard, sql.DEFAULT_GOODBYE)


@user_admin
@typing_action
def welcome(update, context):
    chat = update.effective_chat
    args = context.args
    reply = update.message.message_id
    # if no args, show current replies.
    if len(args) == 0 or args[0].lower() == "noformat":
        noformat = args and args[0].lower() == "noformat"
        pref, welcome_m, cust_content, welcome_type = sql.get_welc_pref(chat.id)
        update.effective_message.reply_text(
            "This chat has it's welcome setting set to: `{}`.\n*The welcome message "
            "(not filling the {{}}) is:*".format(pref),
            parse_mode=ParseMode.MARKDOWN,
        )

        buttons = sql.get_welc_buttons(chat.id)
        if welcome_type == sql.Types.BUTTON_TEXT or welcome_type == sql.Types.TEXT:
            if noformat:
                welcome_m += revert_buttons(buttons)
                send_message(update.effective_message, welcome_m)

            else:
                if buttons:
                    keyb = build_keyboard(buttons)
                    keyboard = InlineKeyboardMarkup(keyb)
                else:
                    keyboard = None

                send(update, welcome_m, keyboard, sql.DEFAULT_WELCOME)

        else:
            if noformat:
                welcome_m += revert_buttons(buttons)
                ENUM_FUNC_MAP[welcome_type](chat.id, cust_content, caption=welcome_m)

            else:
                if buttons:
                    keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                    keyboard = InlineKeyboardMarkup(keyb)
                else:
                    keyboard = None

                if ENUM_FUNC_MAP[welcome_type] == dispatcher.bot.send_sticker:
                    ENUM_FUNC_MAP[welcome_type](
                        chat.id,
                        cust_content,
                        reply_to_message_id=reply,
                        reply_markup=keyboard,
                    )
                else:
                    ENUM_FUNC_MAP[welcome_type](
                        chat.id,
                        cust_content,
                        caption=welcome_m,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.MARKDOWN,
                    )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_welc_preference(str(chat.id), True)
            update.effective_message.reply_text("I'll be polite!")

        elif args[0].lower() in ("off", "no"):
            sql.set_welc_preference(str(chat.id), False)
            update.effective_message.reply_text("I'm sulking, not gonna greet anymore.")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text(
                "I understand 'on/yes' or 'off/no' only!"
            )


@user_admin
@typing_action
def goodbye(update, context):
    chat = update.effective_chat
    args = context.args

    if len(args) == 0 or args[0] == "noformat":
        noformat = args and args[0] == "noformat"
        pref, goodbye_m, goodbye_type = sql.get_gdbye_pref(chat.id)
        update.effective_message.reply_text(
            "This chat has it's goodbye setting set to: `{}`.\n*The goodbye  message "
            "(not filling the {{}}) is:*".format(pref),
            parse_mode=ParseMode.MARKDOWN,
        )

        if goodbye_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_gdbye_buttons(chat.id)
            if noformat:
                goodbye_m += revert_buttons(buttons)
                update.effective_message.reply_text(goodbye_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, goodbye_m, keyboard, sql.DEFAULT_GOODBYE)

        else:
            if noformat:
                ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)

            else:
                ENUM_FUNC_MAP[goodbye_type](
                    chat.id, goodbye_m, parse_mode=ParseMode.MARKDOWN
                )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_gdbye_preference(str(chat.id), True)
            update.effective_message.reply_text("I'll be sorry when people leave!")

        elif args[0].lower() in ("off", "no"):
            sql.set_gdbye_preference(str(chat.id), False)
            update.effective_message.reply_text("They leave, they're dead to me.")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text(
                "I understand 'on/yes' or 'off/no' only!"
            )


@user_admin
@loggable
@typing_action
def set_welcome(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_welcome(chat.id, content, text, data_type, buttons)
    msg.reply_text("Successfully set custom welcome message!")

    return (
        "<b>{}:</b>"
        "\n#SET_WELCOME"
        "\n<b>Admin:</b> {}"
        "\nSet the welcome message.".format(
            escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@user_admin
@loggable
@typing_action
def reset_welcome(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    sql.set_custom_welcome(chat.id, None, sql.DEFAULT_WELCOME, sql.Types.TEXT)
    update.effective_message.reply_text(
        "Successfully reset welcome message to default!"
    )
    return (
        "<b>{}:</b>"
        "\n#RESET_WELCOME"
        "\n<b>Admin:</b> {}"
        "\nReset the welcome message to default.".format(
            escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@user_admin
@loggable
@typing_action
def set_goodbye(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_gdbye(chat.id, content or text, data_type, buttons)
    msg.reply_text("Successfully set custom goodbye message!")
    return (
        "<b>{}:</b>"
        "\n#SET_GOODBYE"
        "\n<b>Admin:</b> {}"
        "\nSet the goodbye message.".format(
            escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@user_admin
@loggable
@typing_action
def reset_goodbye(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
    update.effective_message.reply_text(
        "Successfully reset goodbye message to default!"
    )
    return (
        "<b>{}:</b>"
        "\n#RESET_GOODBYE"
        "\n<b>Admin:</b> {}"
        "\nReset the goodbye message.".format(
            escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@user_admin
@loggable
@typing_action
def welcomemute(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    if len(args) >= 1:
        if args[0].lower() in ("off", "no"):
            sql.set_welcome_mutes(chat.id, False)
            msg.reply_text("I will no longer mute people on joining!")
            return (
                "<b>{}:</b>"
                "\n#WELCOME_MUTE"
                "\n<b>• Admin:</b> {}"
                "\nHas toggled welcome mute to <b>OFF</b>.".format(
                    escape(chat.title), mention_html(user.id, user.first_name)
                )
            )
        elif args[0].lower() in ("soft"):
            sql.set_welcome_mutes(chat.id, "soft")
            msg.reply_text(
                "I will restrict user's permission to send media for 24 hours"
            )
            return (
                "<b>{}:</b>"
                "\n#WELCOME_MUTE"
                "\n<b>• Admin:</b> {}"
                "\nHas toggled welcome mute to <b>SOFT</b>.".format(
                    escape(chat.title), mention_html(user.id, user.first_name)
                )
            )
        elif args[0].lower() in ("strong"):
            sql.set_welcome_mutes(chat.id, "strong")
            msg.reply_text(
                "I will now mute people when they join and"
                " click on the button to be unmuted."
            )
            return (
                "<b>{}:</b>"
                "\n#WELCOME_MUTE"
                "\n<b>• Admin:</b> {}"
                "\nHas toggled welcome mute to <b>STRONG</b>.".format(
                    escape(chat.title), mention_html(user.id, user.first_name)
                )
            )
        else:
            msg.reply_text(
                "Please enter `off`/`on`/`soft`/`strong`!",
                parse_mode=ParseMode.MARKDOWN,
            )
            return ""
    else:
        curr_setting = sql.welcome_mutes(chat.id)
        reply = "\n Give me a setting! Choose one of: `off`/`no` or `soft` or `strong` only! \nCurrent setting: `{}`"
        msg.reply_text(reply.format(curr_setting), parse_mode=ParseMode.MARKDOWN)
        return ""


@user_admin
@loggable
@typing_action
def clean_welcome(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if not args:
        clean_pref = sql.get_clean_pref(chat.id)
        if clean_pref:
            update.effective_message.reply_text(
                "I should be deleting welcome messages up to two days old."
            )
        else:
            update.effective_message.reply_text(
                "I'm currently not deleting old welcome messages!"
            )
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_clean_welcome(str(chat.id), True)
        update.effective_message.reply_text("I'll try to delete old welcome messages!")
        return (
            "<b>{}:</b>"
            "\n#CLEAN_WELCOME"
            "\n<b>Admin:</b> {}"
            "\nHas toggled clean welcomes to <code>ON</code>.".format(
                escape(chat.title), mention_html(user.id, user.first_name)
            )
        )
    elif args[0].lower() in ("off", "no"):
        sql.set_clean_welcome(str(chat.id), False)
        update.effective_message.reply_text("I won't delete old welcome messages.")
        return (
            "<b>{}:</b>"
            "\n#CLEAN_WELCOME"
            "\n<b>Admin:</b> {}"
            "\nHas toggled clean welcomes to <code>OFF</code>.".format(
                escape(chat.title), mention_html(user.id, user.first_name)
            )
        )
    else:
        # idek what you're writing, say yes or no
        update.effective_message.reply_text("I understand 'on/yes' or 'off/no' only!")
        return ""


@user_admin
@typing_action
def cleanservice(update, context):
    chat = update.effective_chat
    args = context.args
    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var == "no" or var == "off":
                sql.set_clean_service(chat.id, False)
                update.effective_message.reply_text(
                    "Turned off service messages cleaning."
                )
            elif var == "yes" or var == "on":
                sql.set_clean_service(chat.id, True)
                update.effective_message.reply_text(
                    "Turned on service messages cleaning!"
                )
            else:
                update.effective_message.reply_text(
                    "Invalid option", parse_mode=ParseMode.MARKDOWN
                )
        else:
            update.effective_message.reply_text(
                "Usage is on/yes or off/no", parse_mode=ParseMode.MARKDOWN
            )
    else:
        curr = sql.clean_service(chat.id)
        if curr:
            update.effective_message.reply_text(
                "Welcome clean service is : on", parse_mode=ParseMode.MARKDOWN
            )
        else:
            update.effective_message.reply_text(
                "Welcome clean service is : off", parse_mode=ParseMode.MARKDOWN
            )


def user_button(update, context):
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    match = re.match(r"user_join_\((.+?)\)", query.data)
    message = update.effective_message
    db_checks = sql.set_human_checks(user.id, chat.id)
    join_user = int(match.group(1))

    if join_user == user.id:
        query.answer(text="Yus! You're a human, Unmuted!")
        context.bot.restrict_chat_member(
            chat.id,
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        context.bot.deleteMessage(chat.id, message.message_id)
        db_checks
    else:
        query.answer(text="You're not allowed to do this!")


WELC_HELP_TXT = (
    "Your group's welcome/goodbye messages can be personalised in multiple ways. If you want the messages"
    " to be individually generated, like the default welcome message is, you can use *these* variables:\n"
    " - `{{first}}`: this represents the user's *first* name\n"
    " - `{{last}}`: this represents the user's *last* name. Defaults to *first name* if user has no "
    "last name.\n"
    " - `{{fullname}}`: this represents the user's *full* name. Defaults to *first name* if user has no "
    "last name.\n"
    " - `{{username}}`: this represents the user's *username*. Defaults to a *mention* of the user's "
    "first name if has no username.\n"
    " - `{{mention}}`: this simply *mentions* a user - tagging them with their first name.\n"
    " - `{{id}}`: this represents the user's *id*\n"
    " - `{{count}}`: this represents the user's *member number*.\n"
    " - `{{chatname}}`: this represents the *current chat name*.\n"
    "\nEach variable MUST be surrounded by `{{}}` to be replaced.\n"
    "Welcome messages also support markdown, so you can make any elements bold/italic/code/links. "
    "Buttons are also supported, so you can make your welcomes look awesome with some nice intro "
    "buttons.\n"
    "To create a button linking to your rules, use this: `[Rules](buttonurl://t.me/{}?start=group_id)`. "
    "Simply replace `group_id` with your group's id, which can be obtained via /id, and you're good to "
    "go. Note that group ids are usually preceded by a `-` sign; this is required, so please don't "
    "remove it.\n"
    "If you're feeling fun, you can even set images/gifs/videos/voice messages as the welcome message by "
    "replying to the desired media, and calling /setwelcome.".format(
        dispatcher.bot.username
    )
)


@user_admin
@typing_action
def welcome_help(update, context):
    update.effective_message.reply_text(WELC_HELP_TXT, parse_mode=ParseMode.MARKDOWN)


# TODO: get welcome data from group butler snap
# def __import_data__(chat_id, data):
#     welcome = data.get('info', {}).get('rules')
#     welcome = welcome.replace('$username', '{username}')
#     welcome = welcome.replace('$name', '{fullname}')
#     welcome = welcome.replace('$id', '{id}')
#     welcome = welcome.replace('$title', '{chatname}')
#     welcome = welcome.replace('$surname', '{lastname}')
#     welcome = welcome.replace('$rules', '{rules}')
#     sql.set_custom_welcome(chat_id, welcome, sql.Types.TEXT)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    welcome_pref = sql.get_welc_pref(chat_id)[0]
    goodbye_pref = sql.get_gdbye_pref(chat_id)[0]
    clean_welc_pref = sql.get_clean_pref(chat_id)
    welc_mutes_pref = sql.get_welc_mutes_pref(chat_id)
    return (
        "This chat has it's welcome preference set to `{}`.\n"
        "It's goodbye preference is `{}`. \n\n"
        "*Service preferences:*\n"
        "\nClean welcome: `{}`"
        "\nWelcome mutes: `{}`".format(
            welcome_pref, goodbye_pref, clean_welc_pref, welc_mutes_pref
        )
    )


__help__ = """
{}

*Admin only:*
 × /welcome <on/off>: enable/disable Welcome messages.
 × /welcome: Shows current welcome settings.
 × /welcome noformat: Shows current welcome settings, without the formatting - useful to recycle your welcome messages!
 × /goodbye -> Same usage and args as /welcome.
 × /setwelcome <sometext>: Sets a custom welcome message. If used replying to media, uses that media.
 × /setgoodbye <sometext>: Sets a custom goodbye message. If used replying to media, uses that media.
 × /resetwelcome: Resets to the default welcome message.
 × /resetgoodbye: Resets to the default goodbye message.
 × /cleanwelcome <on/off>: On new member, try to delete the previous welcome message to avoid spamming the chat.
 × /cleanservice <on/off>: Clean 'user is joined' service messages automatically.
 × /welcomemute <off/soft/strong>: All users that join, get muted; a button gets added to the welcome message for them to unmute themselves. \
This proves they aren't a bot! soft - restricts users ability to post media for 24 hours. strong - mutes on join until they prove they're not bots.
 × /welcomehelp: View more formatting information for custom welcome/goodbye messages.

Buttons in welcome messages are made easy, everyone hates URLs visible. With button links you can make your chats look more \
tidy and simplified.

An example of using buttons:
You can create a button using `[button text](buttonurl://example.com)`.

If you wish to add more than 1 buttons simply do the following:
`[Button 1](buttonurl://example.com)`
`[Button 2](buttonurl://github.com:same)`
`[Button 3](buttonurl://google.com)`

The `:same` end of the link merges 2 buttons on same line as 1 button, resulting in 3rd button to be separated \
from same line.

Tip: Buttons must be placed at the end of welcome messages.
""".format(
    WELC_HELP_TXT
)

__mod_name__ = "Greetings"

NEW_MEM_HANDLER = MessageHandler(
    Filters.status_update.new_chat_members, new_member, run_async=True
)
LEFT_MEM_HANDLER = MessageHandler(
    Filters.status_update.left_chat_member, left_member, run_async=True
)
WELC_PREF_HANDLER = CommandHandler(
    "welcome", welcome, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
GOODBYE_PREF_HANDLER = CommandHandler(
    "goodbye", goodbye, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
SET_WELCOME = CommandHandler(
    "setwelcome", set_welcome, filters=Filters.chat_type.groups, run_async=True
)
SET_GOODBYE = CommandHandler(
    "setgoodbye", set_goodbye, filters=Filters.chat_type.groups, run_async=True
)
RESET_WELCOME = CommandHandler(
    "resetwelcome", reset_welcome, filters=Filters.chat_type.groups, run_async=True
)
RESET_GOODBYE = CommandHandler(
    "resetgoodbye", reset_goodbye, filters=Filters.chat_type.groups, run_async=True
)
CLEAN_WELCOME = CommandHandler(
    "cleanwelcome",
    clean_welcome,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
WELCOMEMUTE_HANDLER = CommandHandler(
    "welcomemute",
    welcomemute,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
CLEAN_SERVICE_HANDLER = CommandHandler(
    "cleanservice",
    cleanservice,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help, run_async=True)
BUTTON_VERIFY_HANDLER = CallbackQueryHandler(
    user_button, pattern=r"user_join_", run_async=True
)

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(WELC_PREF_HANDLER)
dispatcher.add_handler(GOODBYE_PREF_HANDLER)
dispatcher.add_handler(SET_WELCOME)
dispatcher.add_handler(SET_GOODBYE)
dispatcher.add_handler(RESET_WELCOME)
dispatcher.add_handler(RESET_GOODBYE)
dispatcher.add_handler(CLEAN_WELCOME)
dispatcher.add_handler(WELCOMEMUTE_HANDLER)
dispatcher.add_handler(CLEAN_SERVICE_HANDLER)
dispatcher.add_handler(BUTTON_VERIFY_HANDLER)
dispatcher.add_handler(WELCOME_HELP)
