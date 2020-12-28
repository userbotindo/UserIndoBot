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
"""Chat permission database."""

from ubotindo.modules.no_sql import get_collection


PERMISSION = get_collection("PERMISSIONS")
RESTRICTIONS = get_collection("RESTRICTIONS")


def init_permissions(chat_id):
    """Set default permission."""
    PERMISSION.insert_one(
        {
            'chat_id': str(chat_id),
            'permissions' : {
                'audio': False,
                'voice': False,
                'contact': False,
                'video': False,
                'document': False,
                'photo': False,
                'sticker': False,
                'gif': False,
                'url': False,
                'bots': False,
                'forward': False,
                'game': False,
                'location': False,
                'rtl': False,
                'button': False,
                'egame': False,
                'inline': False,
            }
        }
    )


def init_restrictions(chat_id):
    """Default chat restriction."""
    RESTRICTIONS.inser_one(
        {
            'chat_id': str(chat_id),
            'restrictions': {
                'messages': False,
                'media': False,
                'other': False,
                'preview': False,
            }
        }
    )


def update_lock(chat_id, locktype, locked):
    curr_perm = PERMISSION.find_one({'chat_id': str(chat_id)})
    if not curr_perm:
        init_permissions(chat_id)

    PERMISSION.update_one(
        {'chat_id': str(chat_id)},
        {"$set": {
            f'permission.{locktype}': locked,
        }},
        upsert=False,  # don't upsert
    )


def update_restriction(chat_id, restr_type, locked):
    curr_restr = RESTRICTIONS.find_one({'chat_id': str(chat_id)})
    if not curr_restr:
        init_restrictions(chat_id)
    if restr_type == "all":
        RESTRICTIONS.update_one(
            {'chat_id': str(chat_id)},
            {"$set": {
                'restrictions.messages' : locked,
                'restrictions.media' : locked,
                'restrictions.other' : locked,
                'restrictions.preview' : locked,
            }},
            upsert=False,
        )
    else:
        RESTRICTIONS.update_one(
            {'chat_id': str(chat_id)},
            {"$set": {
                f'restrictions.{restr_type}' : locked,
            }},
            upsert=False,
        )


def is_locked(chat_id, lock_type) -> bool:
    curr_perm = PERMISSION.find_one({'chat_id': str(chat_id)})

    if not curr_perm:
        return False

    elif lock_type == "sticker":
        return curr_perm["permission"]["sticker"]
    elif lock_type == "photo":
        return curr_perm["permission"]["photo"]
    elif lock_type == "audio":
        return curr_perm["permission"]["audio"]
    elif lock_type == "voice":
        return curr_perm["permission"]["voice"]
    elif lock_type == "contact":
        return curr_perm["permission"]["contact"]
    elif lock_type == "video":
        return curr_perm["permission"]["video"]
    elif lock_type == "document":
        return curr_perm["permission"]["document"]
    elif lock_type == "gif":
        return curr_perm["permission"]["gif"]
    elif lock_type == "url":
        return curr_perm["permission"]["url"]
    elif lock_type == "bots":
        return curr_perm["permission"]["bots"]
    elif lock_type == "forward":
        return curr_perm["permission"]["forward"]
    elif lock_type == "game":
        return curr_perm["permission"]["game"]
    elif lock_type == "location":
        return curr_perm["permission"]["location"]
    elif lock_type == "rtl":
        return curr_perm["permission"]["rtl"]
    elif lock_type == "button":
        return curr_perm["permission"]["button"]
    elif lock_type == "egame":
        return curr_perm["permission"]["egame"]
    elif lock_type == "inline":
        return curr_perm["permission"]["inline"]


def is_restr_locked(chat_id, lock_type):  # Unused func lol
    curr_restr = RESTRICTIONS.find_one({'chat_id': str(chat_id)})

    if not curr_restr:
        return False

    if lock_type == "messages":
        return curr_restr["restrictions"]["messages"]
    elif lock_type == "media":
        return curr_restr["restrictions"]["media"]
    elif lock_type == "other":
        return curr_restr["restrictions"]["other"]
    elif lock_type == "previews":
        return curr_restr["restrictions"]["preview"]
    elif lock_type == "all":
        return (
            curr_restr["restrictions"]["messages"]
            and curr_restr["restrictions"]["media"]
            and curr_restr["restrictions"]["other"]
            and curr_restr["restrictions"]["preview"]
        )


def get_locks(chat_id) -> dict:
    return PERMISSION.find_one({'chat_id': str(chat_id)})


def get_restr(chat_id) -> dict:
    return RESTRICTIONS.find_one({'chat_id': str(chat_id)})


def migrate_chat(old_chat_id, new_chat_id):
    PERMISSION.update_one(
        {'chat_id': old_chat_id},
        {"$set": {'chat_id': new_chat_id}},
    )
    RESTRICTIONS.update_one(
        {'chat_id': old_chat_id},
        {"$set": {'chat_id': new_chat_id}},
    )
