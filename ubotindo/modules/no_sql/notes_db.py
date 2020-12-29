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

# Note: chat_id's are stored as strings because the int is too large to be


from ubotindo.modules.helper_funcs.msg_types import Types
from ubotindo.modules.no_sql import get_collection


NOTES = get_collection("NOTES")
BUTTONS = get_collection("NOTE_URLS")


def add_note_to_db(
    chat_id, note_name, note_data, msgtype, buttons=None, file=None
):
    if not buttons:
        buttons = []

    BUTTONS.delete_one(
        {'chat_id': str(chat_id), 'note_name': note_name}
    )
    NOTES.update_one(
        {'chat_id': str(chat_id), 'name': note_name},
        {"$set": {
            'value': note_data or "",
            'msgtype': msgtype.value,
            'file': file,
        }},
        upsert=True
    )

    for b_name, url, same_line in buttons:
        add_note_button_to_db(chat_id, note_name, b_name, url, same_line)


def get_note(chat_id, note_name):
    return NOTES.find_one(
        {'chat_id': str(chat_id), 'name': note_name},
    )


def rm_note(chat_id, note_name):
    note = NOTES.find_one_and_delete(
        {'chat_id': str(chat_id), 'name': note_name}
    )
    if note:
        BUTTONS.delete_one({'chat_id': str(chat_id), 'note_name': note_name})
        return True
    else:
        return False


def get_all_chat_notes(chat_id):
    return NOTES.find({'chat_id': str(chat_id)}).sort("name", 1)


def add_note_button_to_db(chat_id, note_name, b_name, url, same_line):
    BUTTONS.update_one(
        {'chat_id': chat_id, 'note_name': note_name},
        {'$set': {'name': b_name, 'url': url, 'same_line': same_line}},
        upsert=True
    )


def get_button(chat_id, note_name):
    return BUTTONS.find({'chat_id': str(chat_id), 'note_name': note_name})


def num_notes():
    return NOTES.count_documents({})


def num_chats():
    return len(NOTES.distinct("chat_id"))


def migrate_chat(old_chat_id, new_chat_id):
    NOTES.update_many(
        {'chat_id': str(old_chat_id)},
        {"$set": {'chat_id': str(new_chat_id)}},
    )
    BUTTONS.update_many(
        {'chat_id': str(old_chat_id)},
        {"$set": {'chat_id': str(new_chat_id)}},
    )