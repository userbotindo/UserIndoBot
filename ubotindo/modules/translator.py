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

import json
import os

import requests
from emoji import UNICODE_EMOJI
from google_trans_new import google_translator, LANGUAGES
from gtts import gTTS
from telegram import ChatAction

from ubotindo import dispatcher
from ubotindo.modules.disable import DisableAbleCommandHandler
from ubotindo.modules.helper_funcs.alternate import send_action, typing_action


@typing_action
def gtrans(update, context):
    msg = update.effective_message
    args = context.args
    lang = " ".join(args)
    if not lang:
        lang = "en"
    try:
        translate_text = (
            msg.reply_to_message.text or msg.reply_to_message.caption
        )
    except AttributeError:
        return msg.reply_text("Give me the text to translate!")

    ignore_text = UNICODE_EMOJI.keys()
    for emoji in ignore_text:
        if emoji in translate_text:
            translate_text = translate_text.replace(emoji, "")

    translator = google_translator()
    try:
        translated = translator.translate(translate_text, lang_tgt=lang)
        source_lan = translator.detect(translate_text)[1].title()
        des_lan = LANGUAGES.get(lang).title()
        msg.reply_text(
            "Translated from {} to {}.\n {}".format(
                source_lan, des_lan, translated
            )
        )
    except BaseException:
        msg.reply_text("Error! invalid language code.")


@send_action(ChatAction.RECORD_AUDIO)
def gtts(update, context):
    msg = update.effective_message
    reply = " ".join(context.args)
    if not reply:
        if msg.reply_to_message:
            reply = msg.reply_to_message.text
        else:
            return msg.reply_text(
                "Reply to some message or enter some text to convert it into audio format!"
            )
        for x in "\n":
            reply = reply.replace(x, "")
    try:
        tts = gTTS(reply)
        tts.save("ubotindo.mp3")
        with open("ubotindo.mp3", "rb") as speech:
            msg.reply_audio(speech)
    finally:
        if os.path.isfile("ubotindo.mp3"):
            os.remove("ubotindo.mp3")


# Open API key
API_KEY = "6ae0c3a0-afdc-4532-a810-82ded0054236"
URL = "http://services.gingersoftware.com/Ginger/correct/json/GingerTheText"


@typing_action
def spellcheck(update, context):
    if update.effective_message.reply_to_message:
        msg = update.effective_message.reply_to_message

        params = dict(
            lang="US", clientVersion="2.0", apiKey=API_KEY, text=msg.text
        )

        res = requests.get(URL, params=params)
        changes = json.loads(res.text).get("LightGingerTheTextResult")
        curr_string = ""
        prev_end = 0

        for change in changes:
            start = change.get("From")
            end = change.get("To") + 1
            suggestions = change.get("Suggestions")
            if suggestions:
                # should look at this list more
                sugg_str = suggestions[0].get("Text")
                curr_string += msg.text[prev_end:start] + sugg_str
                prev_end = end

        curr_string += msg.text[prev_end:]
        update.effective_message.reply_text(curr_string)
    else:
        update.effective_message.reply_text(
            "Reply to some message to get grammar corrected text!"
        )


__help__ = """
× /tr or /tl: - To translate to your language, by default language is set to english, use `/tr <lang code>` for some other language!
× /spell: - As a reply to get grammar corrected text of gibberish message.
× /tts: - To some message to convert it into audio format!
"""
__mod_name__ = "Translate"

dispatcher.add_handler(
    DisableAbleCommandHandler(
        ["tr", "tl"], gtrans, pass_args=True, run_async=True
    )
)
dispatcher.add_handler(
    DisableAbleCommandHandler("tts", gtts, pass_args=True, run_async=True)
)
dispatcher.add_handler(
    DisableAbleCommandHandler("spell", spellcheck, run_async=True)
)
