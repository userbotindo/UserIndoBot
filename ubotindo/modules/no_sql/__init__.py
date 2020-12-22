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
"""MongoDB database."""

from pymongo import MongoClient, collection

from ubotindo import MONGO_URI, LOGGER


LOGGER.info("Connecting to MongoDB")

DB_CLIENT = MongoClient(MONGO_URI)

_DB = DB_CLIENT["UbotIndo"]


def get_collection(name: str) -> collection:
    """Get the collection from database."""
    return _DB[name] 
