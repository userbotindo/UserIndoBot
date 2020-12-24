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
"""Afk module: Tell anyone if you away from keyboard."""
import random
from time import sleep

from telegram import MessageEntity
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler

import ubotindo.modules.helper_funcs.fun_strings as fun
from ubotindo import dispatcher
from ubotindo.modules.disable import (
    DisableAbleCommandHandler,
    DisableAbleMessageHandler,
)
from ubotindo.modules.no_sql import afk_db
from ubotindo.modules.users import get_user_id

AFK_GROUP = 7
AFK_REPLY_GROUP = 8


"""This Function to triger bot"""


def afk(update, context):
    args = update.effective_message.text.split(None, 1)

    if not update.effective_user.id:
        return

    if update.effective_user.id in (777000, 1087968824):
        return

    notice = ""
    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
            notice = "\nYour afk reason was shortened to 100 characters."
    else:
        reason = ""

    afk_db.set_afk(update.effective_user.id, reason)
    afkstr = random.choice(fun.AFK)
    msg = update.effective_message
    afksend = msg.reply_text(
        afkstr.format(update.effective_user.first_name, notice)
    )
    sleep(5)
    try:
        afksend.delete()
    except BadRequest:
        return

"""This function to check user afk or not""" 
def no_longer_afk(update, context):
    user = update.effective_user
    message = update.effective_message

    if not user:  # ignore channels
        return

    res = afk_db.rm_afk(user.id)
    if res:
        if message.new_chat_members:  # dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                "{} is here!",
                "{} is back!",
                "{} is now in the chat!",
                "{} is awake!",
                "{} is back online!",
                "{} is finally here!",
                "Welcome back! {}",
                "Where is {}?\nIn the chat!",
            ]
            chosen_option = random.choice(options)
            unafk = update.effective_message.reply_text(
                chosen_option.format(firstname)
            )
            sleep(10)
            unafk.delete()
        except BaseException:
            return


"""This method to tell if user afk"""
def reply_afk(update, context):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
    ):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION])

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type == MessageEntity.MENTION:
                user_id = get_user_id(
                    message.text[ent.offset: ent.offset + ent.length]
                )
                if not user_id:
                    # Should never happen, since for a user to become AFK they
                    # must have spoken. Maybe changed username?
                    return

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

                try:
                    chat = bot.get_chat(user_id)
                except BadRequest:
                    print(
                        "Error: Could not fetch userid {} for AFK module".format(
                            user_id
                        )
                    )
                    return
                fst_name = chat.first_name

            else:
                return

            check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_afk(update, context, user_id, fst_name, userc_id):
    if afk_db.is_afk(user_id):
        user = afk_db.check_afk_status(user_id)
        if user is None:
            return  # sanity check
        if not user["reason"]:
            if int(userc_id) == int(user_id):
                return
            res = "{} is afk".format(fst_name)
            replafk = update.effective_message.reply_text(res)
        else:
            if int(userc_id) == int(user_id):
                return
            res = "<b>{}</b> is away from keyboard! says it's because of <b>Reason:</b> <code>{}</code>".format(
                fst_name, user["reason"])
            replafk = update.effective_message.reply_text(
                res, parse_mode="html"
            )
        sleep(10)
        try:
            replafk.delete()
        except BadRequest:
            return


def __gdpr__(user_id):
    afk_db.rm_afk(user_id)


__help__ = """
When marked as AFK, any mentions will be replied to with a message to say you're not available!

 × /afk <reason>: Mark yourself as AFK.
 × brb <reason>: Same as the afk command - but not a command.
"""


AFK_HANDLER = DisableAbleCommandHandler("afk", afk, run_async=True)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(
    Filters.regex("(?i)brb"), afk, friendly="afk", run_async=True
)
NO_AFK_HANDLER = MessageHandler(
    Filters.all, no_longer_afk, run_async=True
)
AFK_REPLY_HANDLER = MessageHandler(
    Filters.all & Filters.chat_type.groups & ~Filters.update.edited_message,
    reply_afk,
    run_async=True,
)


dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)


__mod_name__ = "AFK"
__command_list__ = ["afk"]
__handlers__ = [
    (AFK_HANDLER, AFK_GROUP),
    (AFK_REGEX_HANDLER, AFK_GROUP),
    (NO_AFK_HANDLER, AFK_GROUP),
    (AFK_REPLY_HANDLER, AFK_REPLY_GROUP),
]
