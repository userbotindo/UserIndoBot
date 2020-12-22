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
"""Group disabled commands database."""

from ubotindo.modules.no_sql import get_collection

DISABLED_COMMANDS = get_collection("DISABLED_COMMANDS")

DISABLED = {}


def disable_command(chat_id, disable) -> bool:
    data = DISABLED_COMMANDS.find_one(
        {'chat_id': chat_id, 'command': disable})
    if not data:
        DISABLED.setdefault(str(chat_id), set()).add(disable)

        DISABLED_COMMANDS.insert_one(
            {'chat_id': chat_id, 'command': disable})
        return True
    return False


def enable_command(chat_id, enable) -> bool:
    data = DISABLED_COMMANDS.find_one(
        {'chat_id': chat_id, 'command':  enable}
    )
    if data:
        if enable in DISABLED.get(str(chat_id)):  # sanity check
            DISABLED.setdefault(str(chat_id), set()).remove(enable)

        DISABLED_COMMANDS.delete_one(
            {'chat_id': chat_id, 'command': enable}
        )
        return True
    return False


def is_command_disabled(chat_id, cmd) -> bool:
    return cmd in DISABLED.get(str(chat_id), set())


def get_all_disabled(chat_id) -> dict:
    return DISABLED.get(str(chat_id), set())


def num_chats() -> int:
    chats = DISABLED_COMMANDS.distinct('chat_id')
    return len(chats)


def num_disabled() -> int:
    return DISABLED_COMMANDS.count_documents({})


def migrate_chat(old_chat_id, new_chat_id) -> None:
    DISABLED_COMMANDS.update_many(
        {'chat_id': old_chat_id}, {"$set": {'chat_id': new_chat_id}}
    )

    if str(old_chat_id) in DISABLED:
        DISABLED[str(old_chat_id)] = DISABLED.get(str(old_chat_id), set())


def __load_disabled_commands() -> None:
    global DISABLED
    all_chats = DISABLED_COMMANDS.find()
    for chat in all_chats:
        DISABLED.setdefault(chat["chat_id"], set()).add(chat["command"])


__load_disabled_commands()
