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

import html
import os

from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, MessageHandler
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

from ubotindo import dispatcher
from ubotindo.modules.connection import connected
from ubotindo.modules.disable import DisableAbleCommandHandler
from ubotindo.modules.helper_funcs.admin_rights import (
    user_can_changeinfo,
    user_can_pin,
    user_can_promote,
)
from ubotindo.modules.helper_funcs.alternate import typing_action
from ubotindo.modules.helper_funcs.chat_status import (
    bot_admin,
    can_pin,
    can_promote,
    user_admin,
)
from ubotindo.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from ubotindo.modules.log_channel import loggable
from ubotindo.modules.sql import admin_sql as sql


@run_async
@bot_admin
@can_promote
@user_admin
@loggable
@typing_action
def promote(update, context):
    chat_id = update.effective_chat.id
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if user_can_promote(chat, user, context.bot.id) is False:
        message.reply_text("You don't have enough rights to promote someone!")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("mention one.... 🤷🏻‍♂.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == "administrator" or user_member.status == "creator":
        message.reply_text("This person is already an admin...!")
        return ""

    if user_id == context.bot.id:
        message.reply_text("I hope, if i could promote myself!")
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(context.bot.id)

    context.bot.promoteChatMember(
        chat_id,
        user_id,
        can_change_info=bot_member.can_change_info,
        can_post_messages=bot_member.can_post_messages,
        can_edit_messages=bot_member.can_edit_messages,
        can_delete_messages=bot_member.can_delete_messages,
        can_invite_users=bot_member.can_invite_users,
        can_restrict_members=bot_member.can_restrict_members,
        can_pin_messages=bot_member.can_pin_messages,
    )

    message.reply_text("Promoted🧡")
    return (
        "<b>{}:</b>"
        "\n#PROMOTED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {}".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(user_member.user.id, user_member.user.first_name),
        )
    )


@run_async
@bot_admin
@can_promote
@user_admin
@loggable
@typing_action
def demote(update, context):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_promote(chat, user, context.bot.id) is False:
        message.reply_text("You don't have enough rights to demote someone!")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("mention one.... 🤷🏻‍♂.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == "creator":
        message.reply_text("I'm not gonna demote Creator this group.... 🙄")
        return ""

    if not user_member.status == "administrator":
        message.reply_text(
            "How I'm supposed to demote someone who is not even an admin!"
        )
        return ""

    if user_id == context.bot.id:
        message.reply_text("Yeahhh... Not gonna demote myself!")
        return ""

    try:
        context.bot.promoteChatMember(
            int(chat.id),
            int(user_id),
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
        )
        message.reply_text("Successfully demoted!")
        return (
            "<b>{}:</b>"
            "\n#DEMOTED"
            "\n<b>Admin:</b> {}"
            "\n<b>User:</b> {}".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                mention_html(user_member.user.id, user_member.user.first_name),
            )
        )

    except BadRequest:
        message.reply_text(
            "Failed to demote. I might not be admin, or the admin status was appointed by another "
            "user, so I can't act upon them!"
        )
        return ""


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
@typing_action
def pin(update, context):
    args = context.args
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    if user_can_pin(chat, user, context.bot.id) is False:
        message.reply_text("You are missing rights to pin a message!")
        return ""

    is_silent = True
    if len(args) >= 1:
        is_silent = not (
            args[0].lower() == "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            context.bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return (
            "<b>{}:</b>"
            "\n#PINNED"
            "\n<b>Admin:</b> {}".format(
                html.escape(chat.title), mention_html(user.id, user.first_name)
            )
        )

    return ""


@can_pin
@user_admin
@run_async
def permanent_pin_set(update, context) -> str:
    user = update.effective_user
    chat = update.effective_chat
    args = context.args
    bot = context.bot

    conn = connected(bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        dispatcher.bot.getChat(conn).title
        if not args:
            get_permapin = sql.get_permapin(chat_id)
            text_maker = "Permanent pin is currently set:`{}`".format(
                bool(int(get_permapin))
            )
            if get_permapin:
                if chat.username:
                    old_pin = "https://t.me/{}/{}".format(chat.username, get_permapin)
                else:
                    old_pin = "https://t.me/c/{}/{}".format(
                        str(chat.id)[4:], get_permapin
                    )
                text_maker += "\nTo disable permanent pin: `/permanentpin off`"
                text_maker += "\n\n[Permanent pin message is here]({})".format(old_pin)
                update.effective_message.reply_text(text_maker, parse_mode="markdown")
            return ""

        prev_message = args[0]
        if prev_message == "off":
            sql.set_permapin(chat_id, 0)
            update.effective_message.reply_text("Permanently pin has been disabled!")
            return
        if "/" in prev_message:
            prev_message = prev_message.split("/")[-1]
    else:
        if update.effective_message.chat.type == "private":
            update.effective_message.reply_text(
                "You can do this command on groups, not on PM!!!"
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        update.effective_message.chat.title
        if update.effective_message.reply_to_message:
            prev_message = update.effective_message.reply_to_message.message_id
        elif len(args) >= 1 and args[0] == "off":
            sql.set_permapin(chat.id, 0)
            update.effective_message.reply_text("Permanently pin has been disabled!")
            return
        else:
            get_permapin = sql.get_permapin(chat.id)
            text_maker = "Current permanent pin: `{}`".format(bool(int(get_permapin)))
            if get_permapin:
                if chat.username:
                    old_pin = "https://t.me/{}/{}".format(chat.username, get_permapin)
                else:
                    old_pin = "https://t.me/c/{}/{}".format(
                        str(chat.id)[4:], get_permapin
                    )
                text_maker += "\nTo disable permanent pin: `/permanentpin off`"
                text_maker += "\n\n[Permanent pin message is here]({})".format(old_pin)
            update.effective_message.reply_text(text_maker, parse_mode="markdown")
            return ""

    is_group = chat.type != "private" and chat.type != "channel"

    if prev_message and is_group:
        sql.set_permapin(chat.id, prev_message)
        update.effective_message.reply_text("Permanent Pin Set successfully!")
        return (
            "<b>{}:</b>"
            "\n#PERMANENT_PIN"
            "\n<b>Admin:</b> {}".format(
                html.escape(chat.title), mention_html(user.id, user.first_name)
            )
        )

    return ""


@run_async
def permanent_pin(update, context):
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    bot = context.bot

    get_permapin = sql.get_permapin(chat.id)
    if get_permapin and not user.id == bot.id:
        try:
            to_del = bot.pinChatMessage(
                chat.id, get_permapin, disable_notification=True
            )
        except BadRequest:
            sql.set_permapin(chat.id, 0)
            if chat.username:
                old_pin = "https://t.me/{}/{}".format(chat.username, get_permapin)
            else:
                old_pin = "https://t.me/c/{}/{}".format(str(chat.id)[4:], get_permapin)
            message.reply_text(
                "*Permanent pin error:*\nI can't pin messages here!\nMake sure I'm admin and can pin messages.\n\nPermanent pin disabled now, [here is your old pinned message]({})".format(
                    old_pin
                ),
                parse_mode="markdown",
            )
            return

        if to_del:
            try:
                bot.deleteMessage(chat.id, message.message_id + 1)
            except BadRequest:
                print("Permanent pin error: cannot delete pin msg")


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
@typing_action
def unpin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if user_can_pin(chat, user, context.bot.id) is False:
        message.reply_text("You are missing rights to unpin a message!")
        return ""

    try:
        context.bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    return (
        "<b>{}:</b>"
        "\n#UNPINNED"
        "\n<b>Admin:</b> {}".format(
            html.escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@run_async
@bot_admin
@user_admin
@typing_action
def invite(update, context):
    user = update.effective_user
    msg = update.effective_message
    chat = update.effective_chat
    context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
    else:
        if msg.chat.type == "private":
            msg.reply_text("This command is meant to use in chat not in PM")
            return ""
        chat = update.effective_chat

    if chat.username:
        msg.reply_text(chat.username)
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(context.bot.id)
        if bot_member.can_invite_users:
            invitelink = context.bot.exportChatInviteLink(chat.id)
            msg.reply_text(invitelink)
        else:
            msg.reply_text(
                "I don't have access to the invite link, try changing my permissions!"
            )
    else:
        msg.reply_text(
            "I can only give you invite links for supergroups and channels, sorry!"
        )


@run_async
@typing_action
def adminlist(update, context):
    administrators = update.effective_chat.get_administrators()
    text = "Admins in <b>{}</b>:".format(update.effective_chat.title or "this chat")
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = f"{(mention_html(user.id, user.first_name))}"
        if status == "creator":
            text += "\n 🦁 Creator:"
            text += "\n • {} \n\n 🦊 Admin:".format(name)
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = f"{(mention_html(user.id, user.first_name))}"
        if status == "administrator":
            text += "\n • {}".format(name)
    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
@bot_admin
@can_promote
@user_admin
@typing_action
def set_title(update, context):
    args = context.args
    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except Exception:
        return

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    if user_member.status == "creator":
        message.reply_text(
            "This person CREATED the chat, how can i set custom title for him?"
        )
        return

    if not user_member.status == "administrator":
        message.reply_text(
            "Can't set title for non-admins!\nPromote them first to set custom title!"
        )
        return

    if user_id == context.bot.id:
        message.reply_text(
            "I can't set my own title myself! Get the one who made me admin to do it for me."
        )
        return

    if not title:
        message.reply_text("Setting blank title doesn't do anything!")
        return

    if len(title) > 16:
        message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters."
        )

    try:
        context.bot.set_chat_administrator_custom_title(chat.id, user_id, title)
        message.reply_text(
            "Sucessfully set title for <b>{}</b> to <code>{}</code>!".format(
                user_member.user.first_name or user_id, title[:16]
            ),
            parse_mode=ParseMode.HTML,
        )

    except BadRequest:
        message.reply_text("I can't set custom title for admins that I didn't promote!")


@run_async
@bot_admin
@user_admin
@typing_action
def setchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("You are missing right to change group info!")
        return

    if msg.reply_to_message:
        if msg.reply_to_message.photo:
            pic_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            pic_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("You can only set some photo as chat pic!")
            return
        dlmsg = msg.reply_text("Just a sec...")
        tpic = context.bot.get_file(pic_id)
        tpic.download("gpic.png")
        try:
            with open("gpic.png", "rb") as chatp:
                context.bot.set_chat_photo(int(chat.id), photo=chatp)
                msg.reply_text("Successfully set new chatpic!")
        except BadRequest as excp:
            msg.reply_text(f"Error! {excp.message}")
        finally:
            dlmsg.delete()
            if os.path.isfile("gpic.png"):
                os.remove("gpic.png")
    else:
        msg.reply_text("Reply to some photo or file to set new chat pic!")


@run_async
@bot_admin
@user_admin
@typing_action
def rmchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("You don't have enough rights to delete group photo")
        return
    try:
        context.bot.delete_chat_photo(int(chat.id))
        msg.reply_text("Successfully deleted chat's profile photo!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@run_async
@bot_admin
@user_admin
@typing_action
def setchat_title(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("You don't have enough rights to change chat info!")
        return

    title = " ".join(args)
    if not title:
        msg.reply_text("Enter some text to set new title in your chat!")
        return

    try:
        context.bot.set_chat_title(int(chat.id), str(title))
        msg.reply_text(
            f"Successfully set <b>{title}</b> as new chat title!",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@run_async
@bot_admin
@user_admin
@typing_action
def set_sticker(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("You're missing rights to change chat info!")

    if msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            return msg.reply_text(
                "You need to reply to some sticker to set chat sticker set!"
            )
        stkr = msg.reply_to_message.sticker.set_name
        try:
            context.bot.set_chat_sticker_set(chat.id, stkr)
            msg.reply_text(f"Successfully set new group stickers in {chat.title}!")
        except BadRequest as excp:
            if excp.message == "Participants_too_few":
                return msg.reply_text(
                    "Sorry, due to telegram restrictions chat needs to have minimum 100 members before they can have group stickers!"
                )
            msg.reply_text(f"Error! {excp.message}.")
    else:
        msg.reply_text("You need to reply to some sticker to set chat sticker set!")


@run_async
@bot_admin
@user_admin
@typing_action
def set_desc(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("You're missing rights to change chat info!")

    tesc = msg.text.split(None, 1)
    if len(tesc) >= 2:
        desc = tesc[1]
    else:
        return msg.reply_text("Setting empty description won't do anything!")
    try:
        if len(desc) > 255:
            return msg.reply_text("Description must needs to be under 255 characters!")
        context.bot.set_chat_description(chat.id, desc)
        msg.reply_text(f"Successfully updated chat description in {chat.title}!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")


def __chat_settings__(chat_id, user_id):
    return "You are *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status
        in ("administrator", "creator")
    )


__help__ = """
Lazy to promote or demote someone for admins? Want to see basic information about chat? \
All stuff about chatroom such as admin lists, pinning or grabbing an invite link can be \
done easily using the bot.

 × /adminlist: list of admins in the chat

*Admin only:*
 × /pin: Silently pins the message replied to - add `loud`, `notify` or `violent` to give notificaton to users.
 × /unpin: Unpins the currently pinned message.
 × /permanentpin: Set a permanent pin for supergroup chat, when an admin or telegram channel change pinned message, bot will change pinned message immediatelly
 × /invitelink: Gets private chat's invitelink.
 × /promote: Promotes the user replied to.
 × /demote: Demotes the user replied to.
 × /settitle: Sets a custom title for an admin which is promoted by bot.
 × /setgpic: As a reply to file or photo to set group profile pic!
 × /delgpic: Same as above but to remove group profile pic.
 × /setgtitle <newtitle>: Sets new chat title in your group.
 × /setsticker: As a reply to some sticker to set it as group sticker set!
 × /setdescription: <description> Sets new chat description in group.

*Note*: To set group sticker set chat must needs to have min 100 members.

An example of promoting someone to admins:
`/promote @username`; this promotes a user to admins.
"""

__mod_name__ = "Admin"

PIN_HANDLER = CommandHandler("pin", pin, pass_args=True, filters=Filters.group)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.group)

PERMANENT_PIN_SET_HANDLER = CommandHandler(
    "permanentpin", permanent_pin_set, pass_args=True, filters=Filters.group
)
PERMANENT_PIN_HANDLER = MessageHandler(
    Filters.status_update.pinned_message | Filters.user(777000), permanent_pin
)

INVITE_HANDLER = CommandHandler("invitelink", invite)
CHAT_PIC_HANDLER = CommandHandler("setgpic", setchatpic, filters=Filters.group)
DEL_CHAT_PIC_HANDLER = CommandHandler("delgpic", rmchatpic, filters=Filters.group)
SETCHAT_TITLE_HANDLER = CommandHandler(
    "setgtitle", setchat_title, filters=Filters.group
)
SETSTICKET_HANDLER = CommandHandler("setsticker", set_sticker, filters=Filters.group)
SETDESC_HANDLER = CommandHandler("setdescription", set_desc, filters=Filters.group)

PROMOTE_HANDLER = CommandHandler(
    "promote", promote, pass_args=True, filters=Filters.group
)
DEMOTE_HANDLER = CommandHandler("demote", demote, pass_args=True, filters=Filters.group)

SET_TITLE_HANDLER = DisableAbleCommandHandler("settitle", set_title, pass_args=True)
ADMINLIST_HANDLER = DisableAbleCommandHandler(
    "adminlist", adminlist, filters=Filters.group
)

dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(PERMANENT_PIN_SET_HANDLER)
dispatcher.add_handler(PERMANENT_PIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(CHAT_PIC_HANDLER)
dispatcher.add_handler(DEL_CHAT_PIC_HANDLER)
dispatcher.add_handler(SETCHAT_TITLE_HANDLER)
dispatcher.add_handler(SETSTICKET_HANDLER)
dispatcher.add_handler(SETDESC_HANDLER)
