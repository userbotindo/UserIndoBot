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

import telegram.ext as tg
from telegram import Update

from ubotindo import LOGGER

try:
    from ubotindo import CUSTOM_CMD
except BaseException:
    CUSTOM_CMD = False

if CUSTOM_CMD:
    CMD_STARTERS = CUSTOM_CMD
    LOGGER.debug("Bot custom command handler = \"%s\"", CMD_STARTERS)
else:
    CMD_STARTERS = "/"


class CustomCommandHandler(tg.CommandHandler):
    def __init__(self, command, callback, **kwargs):
        if "admin_ok" in kwargs:
            del kwargs["admin_ok"]
        super().__init__(command, callback, **kwargs)

    def check_update(self, update):
        if isinstance(update, Update) and update.effective_message:
            message = update.effective_message

            if message.text and len(message.text) > 1:
                fst_word = message.text.split(None, 1)[0]
                if len(fst_word) > 1 and any(
                    fst_word.startswith(start) for start in CMD_STARTERS
                ):
                    args = message.text.split()[1:]
                    command = fst_word[1:].split("@")
                    command.append(
                        message.bot.username
                    )  # in case the command was sent without a username

                    if not (
                        command[0].lower() in self.command
                        and command[1].lower() == message.bot.username.lower()
                    ):
                        return None

                    filter_result = self.filters(update)
                    if filter_result:
                        return args, filter_result
                    else:
                        return False
