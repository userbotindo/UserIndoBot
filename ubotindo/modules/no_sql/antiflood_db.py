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
"""Chat AntiFlood settings"""

from ubotindo.modules.no_sql import get_collection


DEF_COUNT = 0
DEF_LIMIT = 0
DEF_OBJ = (None, DEF_COUNT, DEF_LIMIT)
CHAT_FLOOD = {}

FLOOD_CONTROL = get_collection("ANTIFLOOD")
FLOOD_SETTINGS = get_collection("ANTIFLOOD_SETTING")


def set_flood(chat_id, amount):
    FLOOD_CONTROL.update_one(
        {'chat_id': str(chat_id)},
        {"$set": {'user_id': None, 'limit': amount}},
        upsert=True,
    )
    CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, amount)


def update_flood(chat_id: str, user_id) -> bool:
    if str(chat_id) in CHAT_FLOOD:
        curr_user_id, count, limit = CHAT_FLOOD.get(str(chat_id), DEF_OBJ)

        if limit == 0:  # no antiflood
            return False

        if user_id != curr_user_id or user_id is None:  # other user
            CHAT_FLOOD[str(chat_id)] = (user_id, DEF_COUNT, limit)
            return False

        count += 1
        if count > limit:  # too many msgs, kick
            CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, limit)
            return True

        # default -> update
        CHAT_FLOOD[str(chat_id)] = (user_id, count, limit)
        return False


def get_flood_limit(chat_id):
    return CHAT_FLOOD.get(str(chat_id), DEF_OBJ)[2]


def set_flood_strength(chat_id, flood_type, value):
    """For flood_type
        1 = ban
        2 = kick
        3 = mute
        4 = tban
        5 = tmute
    """
    FLOOD_SETTINGS.update_one(
        {'chat_id': str(chat_id)},
        {"$set": {'flood_type': int(flood_type), 'value': str(value)}},
        upsert=True,
    )


def get_flood_setting(chat_id):
    setting = FLOOD_SETTINGS.find_one({'chat_id': str(chat_id)})
    if setting:
        return setting["flood_type"], setting["value"]
    else:
        return 1, "0"


def migrate_chat(old_chat_id, new_chat_id):
    flood = FLOOD_CONTROL.find_one_and_update(
        {'chat_id': old_chat_id},
        {"$set", {'chat_id': new_chat_id}}
    )
    if flood:
        CHAT_FLOOD[str(new_chat_id)] = CHAT_FLOOD.get(
            str(old_chat_id), DEF_OBJ
        )


def __load_flood_settings():
    global CHAT_FLOOD
    all_chats = FLOOD_CONTROL.find()
    CHAT_FLOOD = {
        chat["chat_id"]: (None, DEF_COUNT, chat["limit"]) for chat in all_chats
    }


__load_flood_settings()