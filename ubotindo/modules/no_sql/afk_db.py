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
"""User(s) AFK database."""

from ubotindo.modules.no_sql import get_collection


AFK_USERS = get_collection("AFK_USERS")
AFK_LIST = set()


def is_afk(user_id) -> bool:
    return user_id in AFK_LIST


def check_afk_status(user_id) -> dict:
    data = AFK_USERS.find_one({'_id': user_id})
    return data


def set_afk(user_id, reason: str="") -> None:
    AFK_USERS.update_one(
        {'_id': user_id},
        {"$set": {'reason': reason}},
        upsert=True)
    __load_afk_users()


def rm_afk(user_id) -> bool:
    data = AFK_USERS.find_one_and_delete({'_id': user_id})
    if data:
        AFK_LIST.remove(user_id)
        return True
    return False


def __load_afk_users()-> None:
    global AFK_LIST
    data = AFK_USERS.find()
    AFK_LIST = {
        x["_id"] for x in data 
    }


__load_afk_users()
