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
"""Chat connection database."""

import time
from typing import Union

from ubotindo.modules.no_sql import get_collection


CHAT_ACCESS_CONNECTION = get_collection("ACCESS_CONNECTION")
CONNECTION = get_collection("CONNECTION")
CONNECTION_HISTORY = get_collection("CONNECTION_HISTORY")

HISTORY_CONNECT = {}


def allow_connect_to_chat(chat_id: Union[str, int]) -> bool:
    chat_setting = CHAT_ACCESS_CONNECTION.find_one({'chat_id': str(chat_id)})
    if chat_setting:
        return chat_setting["allow_connect_to_chat"]
    return False


def set_allow_connect_to_chat(chat_id: Union[str, int], setting: bool):
    CHAT_ACCESS_CONNECTION.update_one(
        {'chat_id': str(chat_id)},
        {"$set": {
            'allow_connect_to_chat': setting
        }},
        upsert=True,
    )


def connect(user_id, chat_id):
    CONNECTION.update_one(
        {'user_id': int(user_id)},
        {"$set": {
            'chat_id': chat_id
        }},
        upsert=True,
    )
    return True


def get_connected_chat(user_id):
    return CONNECTION.find_one({'user_id': int(user_id)})


def curr_connection(chat_id):
    return CONNECTION.find_one({'chat_id': str(chat_id)})


def disconnect(user_id):
    disconnect = CONNECTION.find_one_and_delete(
        {'user_id': int(user_id)}
    )
    return bool(disconnect)


def add_history_conn(user_id, chat_id, chat_name):
    global HISTORY_CONNECT
    conn_time = int(time.time())
    if HISTORY_CONNECT.get(int(user_id)):
        counting = CONNECTION_HISTORY.count_documents(
            {'user_id': str(user_id)}
        )
        getchat_id = {}
        for x in HISTORY_CONNECT[int(user_id)]:
            getchat_id[HISTORY_CONNECT[int(user_id)][x]["chat_id"]] = x
        if chat_id in getchat_id:
            todeltime = getchat_id[str(chat_id)]
            dateold = CONNECTION_HISTORY.find_one_and_delete(
                {'user_id': int(user_id), 'chat_id': str(chat_id)}
            )
            if dateold:
                HISTORY_CONNECT[int(user_id)].pop(todeltime)
        elif counting >= 5:
            todel = list(HISTORY_CONNECT[int(user_id)])
            todel.reverse()
            todel = todel[4:]
            for x in todel:
                chat_old = HISTORY_CONNECT[int(user_id)][x]["chat_id"]
                delold = CONNECTION_HISTORY.find_one_and_delete(
                    {'user_id': int(user_id), 'chat_id': str(chat_old)}
                )
                if delold:
                    HISTORY_CONNECT[int(user_id)].pop(x)
    else:
        HISTORY_CONNECT[int(user_id)] = {}
    CONNECTION_HISTORY.update_one(
        {'user_id': int(user_id), 'chat_id': str(chat_id)},
        {"$set": 
            {'chat_id': str(chat_id), 'chat_name': chat_name, 'conn_time': conn_time}
        },
        upsert=True,
    )
    HISTORY_CONNECT[int(user_id)][conn_time] = {
        "chat_name": chat_name,
        "chat_id": str(chat_id),
    }


def get_history_conn(user_id):
    if not HISTORY_CONNECT.get(int(user_id)):
        HISTORY_CONNECT[int(user_id)] = {}
    return HISTORY_CONNECT[int(user_id)]


def clear_history_conn(user_id):
    global HISTORY_CONNECT
    todel = list(HISTORY_CONNECT[int(user_id)])
    for x in todel:
        chat_old = HISTORY_CONNECT[int(user_id)][x]["chat_id"]
        delold = CONNECTION_HISTORY.find_one_and_delete(
            {'user_id': int(user_id), 'chat_id': str(chat_old)}
        )
        if delold:
            HISTORY_CONNECT[int(user_id)].pop(x)
    return True


def __load_user_history():
    global HISTORY_CONNECT
    qall = CONNECTION_HISTORY.find({})
    HISTORY_CONNECT = {}
    for x in qall:
        check = HISTORY_CONNECT.get(x["user_id"])
        if check is None:
            HISTORY_CONNECT[x["user_id"]] = {}
        HISTORY_CONNECT[x["user_id"]][x["conn_time"]] = {
            "chat_name": x["chat_name"],
            "chat_id": x["chat_id"],
        }


__load_user_history()
