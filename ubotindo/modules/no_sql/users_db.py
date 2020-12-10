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
"""User database utils."""

from ubotindo import dispatcher
from ubotindo.modules.no_sql import get_collection


USERS_DB = get_collection("USERS")
CHATS_DB = get_collection("CHATS")
CHAT_MEMBERS_DB = get_collection("CHAT_MEMBERS")


def update_user(user_id, username, chat_id=None, chat_name=None):
    user = USERS_DB.find_one({'_id': user_id})
    if not user:
        USERS_DB.insert_one({'_id': user_id, 'username': username})
    else:
        USERS_DB.update_one({'_id': user_id}, {"$set": {'username': username}})
    
    if not (chat_id or chat_name):
        return
    
    chat = CHATS_DB.find_one({'_id': chat_id})
    if not chat:
        CHATS_DB.insert_one({'_id': chat_id, 'chat_name': chat_name})
    else:
        CHATS_DB.update_one({'_id': chat_id}, {"$set": {'chat_name': chat_name}})
    
    member = CHAT_MEMBERS_DB.find_one({'chat_id': chat["_id"], 'user_id': user["_id"]})
    if not member:
        CHAT_MEMBERS_DB.insert_one({'chat_id': chat["_id"], 'user_id': user["_id"]})


def get_userid_by_name(username) -> dict:
    return USERS_DB.find({'username': username})


def get_name_by_userid(user_id) -> dict:
    return USERS_DB.find_one({'_id': user_id})


def get_chat_members(chat_id) -> dict:
    return CHAT_MEMBERS_DB.find({'chat_id': chat_id})


def get_all_chats() -> dict:
    return CHATS_DB.find()


def get_all_users() -> dict:
    return USERS_DB.find()


def get_user_num_chats(user_id) -> int:
    return CHAT_MEMBERS_DB.count_documents(
        {'user_id': user_id})


def num_chats() -> int:
    return CHATS_DB.count_documents({})


def num_users() -> int:
    return USERS_DB.count_documents({})


def migrate_chat(old_chat_id, new_chat_id) -> None:
    CHATS_DB.update_one({'_id': old_chat_id}, {"$set": {'_id': new_chat_id}})

    chat_members = (
        CHAT_MEMBERS_DB.find({'chat_id': old_chat_id})
    )
    for member in chat_members:
        CHAT_MEMBERS_DB.update_one({'chat_id': member["chat_id"]}, {"$set": {'chat_id': new_chat_id}})
