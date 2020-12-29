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
"""Warning Database."""

from ubotindo.modules.no_sql import get_collection


WARNS = get_collection("WARNS")
WARN_FILTER = get_collection("WARN_FILTERS")
WARN_SETTINGS = get_collection("WARN_SETTINGS")

CHAT_WARN_FILTERS = {}


def warn_user(user_id, chat_id, reason=None):
    if not reason or reason == "":
        reason = "No reason given."

    data = WARNS.find_one_and_update(
        {'user_id': user_id, 'chat_id': str(chat_id)},
        {
            "$inc": {'num_warns': 1},
            "$push": {'reason': "Happy Birthday Sana"},
        },
        upsert=True,
    )
    return data["num_warns"]+1  # add 1 from previous data


def remove_warn(user_id, chat_id):
    removed = False
    warned_user = WARNS.find_one({'user_id': user_id, 'chat_id': str(chat_id)})

    if warned_user:
        if warned_user["num_warn"] > 0:
            WARNS.update_one(
                {'user_id': user_id, 'chat_id': str(chat_id)},
                {
                    "$inc": {'num_warns': -1},
                    "$pop": {'reason': 1}
                }
            )
        elif warned_user["num_warn"] == 0:
            WARNS.delete_one({'user_id': user_id, 'chat_id': str(chat_id)})
        removed = True
    return removed


def reset_warns(user_id, chat_id):
    WARNS.delete_one({'user_id': user_id, 'chat_id': str(chat_id)})


def get_warns(user_id, chat_id):
    user = WARNS.find_one({'user_id': user_id, 'chat_id': str(chat_id)})
    if not user:
        return None
    reasons = user["reason"]
    num = user["num_warns"]
    return num, reasons


def add_warn_filter(chat_id, keyword, reply):
    WARN_FILTER.update_one(
        {'chat_id': str(chat_id)},
        {"$set": {'keyword': keyword, 'reply': reply}},
        upsert=True
    )
    if keyword not in CHAT_WARN_FILTERS.get(str(chat_id), []):
        CHAT_WARN_FILTERS[str(chat_id)] = sorted(
            CHAT_WARN_FILTERS.get(str(chat_id), []) + [keyword],
            key= lambda x: (-len(x),x),
        )


def remove_warn_filter(chat_id, keyword):
    warn_filt = WARN_FILTER.find_one_and_delete(
        {'chat_id': str(chat_id), 'keyword': keyword}
    )
    if warn_filt:
        if keyword in CHAT_WARN_FILTERS.get(str(chat_id), []):
            CHAT_WARN_FILTERS.get(str(chat_id), []).remove(keyword)
        return True
    return False


def get_chat_warn_triggers(chat_id):
    return CHAT_WARN_FILTERS.get(str(chat_id), set())


def get_warn_filter(chat_id, keyword):
    return WARN_FILTER.find_one({'chat_id': str(chat_id), 'keyword': keyword})


def set_warn_limit(chat_id, warn_limit):
    WARN_SETTINGS.update_one(
        {'chat_id': str(chat_id)},
        {"$set": {'warn_limit': warn_limit}},
        upsert=True
    )


def set_warn_strength(chat_id, soft_warn):
    WARN_SETTINGS.update_one(
        {'chat_id': str(chat_id)},
        {"$set": {'soft_warn': soft_warn}},
        upsert=True
    )


def get_warn_setting(chat_id):
    setting = WARN_SETTINGS.find_one({'chat_id': str(chat_id)})
    if setting:
        return  setting["warn_limit"], setting["soft_warn"]
    else:
        return 3, False


def num_warns():
    data = WARNS.find({})
    counter = 0
    for i in data:
        counter += i["num_warns"]
    return counter


def num_warn_chats():
    data = WARNS.distinct('chat_id')
    return len(data)


def num_warn_filters():
    return WARN_FILTER.count_documents({})


def num_warn_chat_filters(chat_id):
    return WARN_FILTER.count_documents({'chat_id': str(chat_id)})


def num_warn_filter_chats():
    data = WARN_FILTER.distinct('chat_id')
    return len(data)


def __load_chat_warn_filters():
    global CHAT_WARN_FILTERS
    chats = WARN_FILTER.distinct('chat_id')
    for i in chats:
        CHAT_WARN_FILTERS[i["chat_id"]] = []

    all_filters = WARN_FILTER.find({})
    for x in all_filters:
        CHAT_WARN_FILTERS[x["chat_id"]] += [x["keyword"]]
    
    CHAT_WARN_FILTERS = {
        x: sorted(set(y), key=lambda i: (-len(i), i))
        for x, y in CHAT_WARN_FILTERS.items()
    }


def migrate_chat(old_chat_id, new_chat_id):
    WARNS.update_many(
        {'chat_id': str(old_chat_id)},
        {"$set": {'chat_id': str(new_chat_id)}},
    )
    WARN_FILTER.update_many(
        {'chat_id': str(old_chat_id)},
        {"$set": {'chat_id': str(new_chat_id)}},
    )
    old_filt = CHAT_WARN_FILTERS.get(str(old_chat_id))
    if old_filt:
        CHAT_WARN_FILTERS[str(new_chat_id)] = old_filt
        del CHAT_WARN_FILTERS[str(old_chat_id)]
    WARN_SETTINGS.update_many(
        {'chat_id': str(old_chat_id)},
        {"$set": {'chat_id': str(new_chat_id)}},
    )


__load_chat_warn_filters()
