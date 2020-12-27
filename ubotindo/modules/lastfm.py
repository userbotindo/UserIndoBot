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

import time

import requests
from telegram import ParseMode, error
from telegram.ext import CommandHandler

from ubotindo import LASTFM_API_KEY, dispatcher
from ubotindo.modules.no_sql import get_collection
from ubotindo.modules.disable import DisableAbleCommandHandler
from ubotindo.modules.helper_funcs.alternate import typing_action


LASTFM_USER = get_collection("LAST_FM")


@typing_action
def set_user(update, context):
    msg = update.effective_message
    args = context.args
    if args:
        user = update.effective_user.id
        username = " ".join(args)
        if LASTFM_USER.find_one({'_id': user}):
            LASTFM_USER.find_one_and_update(
                {'_id': user}, {"$set": {'username': username}})
            del_msg = msg.reply_text(f"Username updated to {username}!")
        else:
            LASTFM_USER.insert_one({'_id': user, 'username': username})
            del_msg = msg.reply_text(f"Username set as {username}!")

    else:
        del_msg = msg.reply_text(
            "That's not how this works...\nRun /setuser followed by your username!"
        )
    time.sleep(10)
    try:
        del_msg.delete()
    except error.BadRequest:
        return


@typing_action
def clear_user(update, context):
    user = update.effective_user.id
    LASTFM_USER.delete_one({'_id': user})
    clear = update.effective_message.reply_text(
        "Last.fm username successfully cleared from my database!"
    )
    time.sleep(10)
    clear.delete()


@typing_action
def last_fm(update, context):
    msg = update.effective_message
    user = update.effective_user.first_name
    user_id = update.effective_user.id
    data = LASTFM_USER.find_one({'_id': user_id})
    if data is None:
        msg.reply_text("You haven't set your username yet!")
        return
    username = data["username"]
    base_url = "http://ws.audioscrobbler.com/2.0"
    res = requests.get(
        f"{base_url}?method=user.getrecenttracks&limit=3&extended=1&user={username}&api_key={LASTFM_API_KEY}&format=json"
    )
    if not res.status_code == 200:
        msg.reply_text(
            "Hmm... something went wrong.\nPlease ensure that you've set the correct username!"
        )
        return

    try:
        first_track = res.json().get("recenttracks").get("track")[0]
    except IndexError:
        msg.reply_text("You don't seem to have scrobbled any songs...")
        return
    if first_track.get("@attr"):
        # Ensures the track is now playing
        image = first_track.get("image")[3].get(
            "#text")  # Grab URL of 300x300 image
        artist = first_track.get("artist").get("name")
        song = first_track.get("name")
        loved = int(first_track.get("loved"))
        rep = f"{user} is currently listening to:\n"
        if not loved:
            rep += f"🎧  <code>{artist} - {song}</code>"
        else:
            rep += f"🎧  <code>{artist} - {song}</code> (♥️, loved)"
        if image:
            rep += f"<a href='{image}'>\u200c</a>"
    else:
        tracks = res.json().get("recenttracks").get("track")
        track_dict = {tracks[i].get("artist").get(
            "name"): tracks[i].get("name") for i in range(3)}
        rep = f"{user} was listening to:\n"
        for artist, song in track_dict.items():
            rep += f"🎧  <code>{artist} - {song}</code>\n"
        last_user = (
            requests.get(
                f"{base_url}?method=user.getinfo&user={username}&api_key={LASTFM_API_KEY}&format=json"
            )
            .json()
            .get("user")
        )
        scrobbles = last_user.get("playcount")
        rep += f"\n(<code>{scrobbles}</code> scrobbles so far)"

    send = msg.reply_text(rep, parse_mode=ParseMode.HTML)
    time.sleep(60)
    try:
        send.delete()
        msg.delete()
    except error.BadRequest:
        return


def __stats__():
    return "× {} saved Last.FM username.".format(
        LASTFM_USER.count_documents({})
    )


SET_USER_HANDLER = CommandHandler("setuser", set_user, pass_args=True, run_async=True)
CLEAR_USER_HANDLER = CommandHandler("clearuser", clear_user, run_async=True)
LASTFM_HANDLER = DisableAbleCommandHandler("lastfm", last_fm, run_async=True)

dispatcher.add_handler(SET_USER_HANDLER)
dispatcher.add_handler(CLEAR_USER_HANDLER)
dispatcher.add_handler(LASTFM_HANDLER) 