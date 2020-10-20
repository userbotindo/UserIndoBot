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

import datetime
import html
import os
import platform
import subprocess
import time
from platform import python_version

import requests
import speedtest
from psutil import boot_time, cpu_percent, disk_usage, virtual_memory
from spamwatch import __version__ as __sw__
from telegram import ParseMode, __version__
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, run_async

from ubotindo import MESSAGE_DUMP, OWNER_ID, dispatcher
from ubotindo.modules.helper_funcs.alternate import typing_action
from ubotindo.modules.helper_funcs.filters import CustomFilters


@run_async
@typing_action
def leavechat(update, context):
    args = context.args
    msg = update.effective_message
    if args:
        chat_id = int(args[0])

    else:
        msg.reply_text("Bro.. Give Me ChatId And boom!!")
    try:
        titlechat = context.bot.get_chat(chat_id).title
        context.bot.sendMessage(
            chat_id,
            "I'm here trying to survive, but this world is too cruel, goodbye everyone 😌",
        )
        context.bot.leaveChat(chat_id)
        msg.reply_text("I have left the group {}".format(titlechat))

    except BadRequest as excp:
        if excp.message == "bot is not a member of the supergroup chat":
            msg = update.effective_message.reply_text(
                "I'Am not Joined The Group, Maybe You set wrong id or I Already Kicked out"
            )

        else:
            return


@typing_action
@run_async
def ping(update, context):
    msg = update.effective_message
    start_time = time.time()
    message = msg.reply_text("Pinging...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    message.edit_text(
        "*Pong!!!*\n`{}ms`".format(ping_time), parse_mode=ParseMode.MARKDOWN
    )


@run_async
@typing_action
def get_bot_ip(update, context):
    """Sends the bot's IP address, so as to be able to ssh in if necessary.
    OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@run_async
@typing_action
def speedtst(update, context):
    message = update.effective_message
    ed_msg = message.reply_text("Running high speed test . . .")
    test = speedtest.Speedtest()
    test.get_best_server()
    test.download()
    test.upload()
    test.results.share()
    result = test.results.dict()
    context.bot.editMessageText(
        "Download "
        f"{speed_convert(result['download'])} \n"
        "Upload "
        f"{speed_convert(result['upload'])} \n"
        "Ping "
        f"{result['ping']} \n"
        "ISP "
        f"{result['client']['isp']}",
        update.effective_chat.id,
        ed_msg.message_id,
    )


@run_async
@typing_action
def system_status(update, context):
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    status = "<b>======[ SYSTEM INFO ]======</b>\n\n"
    status += "<b>System uptime:</b> <code>" + str(uptime) + "</code>\n"

    uname = platform.uname()
    status += "<b>System:</b> <code>" + str(uname.system) + "</code>\n"
    status += "<b>Node name:</b> <code>" + str(uname.node) + "</code>\n"
    status += "<b>Release:</b> <code>" + str(uname.release) + "</code>\n"
    status += "<b>Version:</b> <code>" + str(uname.version) + "</code>\n"
    status += "<b>Machine:</b> <code>" + str(uname.machine) + "</code>\n"
    status += "<b>Processor:</b> <code>" + str(uname.processor) + "</code>\n\n"

    mem = virtual_memory()
    cpu = cpu_percent()
    disk = disk_usage("/")
    status += "<b>CPU usage:</b> <code>" + str(cpu) + " %</code>\n"
    status += "<b>Ram usage:</b> <code>" + str(mem[2]) + " %</code>\n"
    status += "<b>Storage used:</b> <code>" + str(disk[3]) + " %</code>\n\n"
    status += "<b>Python version:</b> <code>" + python_version() + "</code>\n"
    status += "<b>Library version:</b> <code>" + str(__version__) + "</code>\n"
    status += "<b>Spamwatch API:</b> <code>" + str(__sw__) + "</code>\n"
    context.bot.sendMessage(update.effective_chat.id, status, parse_mode=ParseMode.HTML)


def speed_convert(size):
    """Hi human, you can't read bytes?"""
    power = 2 ** 10
    zero = 0
    units = {0: "", 1: "Kb/s", 2: "Mb/s", 3: "Gb/s", 4: "Tb/s"}
    while size > power:
        size /= power
        zero += 1
    return f"{round(size, 2)} {units[zero]}"


@run_async
@typing_action
def gitpull(update, context):
    sent_msg = update.effective_message.reply_text("Pulling all changes from remote...")
    subprocess.Popen("git pull", stdout=subprocess.PIPE, shell=True)

    sent_msg_text = (
        sent_msg.text
        + "\n\nChanges pulled... I guess..\nContinue to restart with /reboot "
    )
    sent_msg.edit_text(sent_msg_text)


@run_async
@typing_action
def restart(update, context):
    user = update.effective_message.from_user

    update.effective_message.reply_text(
        "Starting a new instance and shutting down this one"
    )

    if MESSAGE_DUMP:
        datetime_fmt = "%H:%M - %d-%m-%Y"
        current_time = datetime.datetime.utcnow().strftime(datetime_fmt)
        message = (
            f"<b>Bot Restarted </b>"
            f"<b>By :</b> <code>{html.escape(user.first_name)}</code>"
            f"<b>\nDate Bot Restart : </b><code>{current_time}</code>"
        )
        context.bot.send_message(
            chat_id=MESSAGE_DUMP,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    os.system("bash start")


IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID))
PING_HANDLER = CommandHandler("ping", ping, filters=CustomFilters.sudo_filter)
SPEED_HANDLER = CommandHandler("speedtest", speedtst, filters=CustomFilters.sudo_filter)
SYS_STATUS_HANDLER = CommandHandler(
    "sysinfo", system_status, filters=CustomFilters.dev_filter
)
LEAVECHAT_HANDLER = CommandHandler(
    ["leavechat", "leavegroup", "leave"],
    leavechat,
    pass_args=True,
    filters=CustomFilters.dev_filter,
)
GITPULL_HANDLER = CommandHandler("gitpull", gitpull, filters=CustomFilters.dev_filter)
RESTART_HANDLER = CommandHandler("reboot", restart, filters=CustomFilters.dev_filter)

dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(SPEED_HANDLER)
dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(SYS_STATUS_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
dispatcher.add_handler(GITPULL_HANDLER)
dispatcher.add_handler(RESTART_HANDLER)
