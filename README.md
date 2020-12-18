# USERINDOBOT

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
[![ForTheBadge built-with-love](http://ForTheBadge.com/images/badges/built-with-love.svg)](https://github.com/UserBotIndo/)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/8bfae649db3742a883e0ac1008755db3)](https://www.codacy.com/gh/userbotindo/UserIndoBot/dashboard?utm_source=github.com&utm_medium=referral&utm_content=userbotindo/UserIndoBot&utm_campaign=Badge_Grade)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://github.com/userbotindo/UserIndoBot/pulls)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/userbotindo/UserIndoBot/graphs/commit-activity)
![logo](https://i.ibb.co/zJdLsyg/Userindobot.png)

A modular telegram Python bot running on python3 with sqlalchemy database.

Originally a simple group management bot with multiple admin features, it has evolved, becoming extremely modular and
simple to use. Note that this project uses a well-known Telegram-bot of its time @BanhammerMarie_bot from Paul Larson as its base.

Can be found on telegram as [UserbotIndo](https://t.me/userbotindobot).

Join the [Group Support](https://t.me/userbotindo) if you just want to stay in the loop about new features or announcements.

## Credits

Skyleebot For Awesome Bot, And This Base in They

Skittbot for Stickers module and memes module.

1maverick1 for many stuff.

AyraHikari for weather modules and some other stuff.

RealAkito for reverse search modules.

MrYacha for connections module

ATechnoHazard for many stuffs

Corsicanu and Nunopenim for android modules

Any other missing Credits can be seen in commits!

## Starting the bot

Once you've set up your database and your configuration (see below) is complete, simply run:

`python3 -m ubotindo`

## Setting up the bot Read this before trying to use

Please make sure to use python3.6 above, as I cannot guarantee everything will work as expected on older Python versions!
This is because markdown parsing is done by iterating through a dict, which is ordered by default in 3.6.

### Configuration

There are two possible ways of configuring your bot: a config.py file, or ENV variables.

The preferred version is to use a `config.py` file, as it makes it easier to see all your settings together.
This file should be placed in your `UserindoBot` folder, alongside the `__main__.py` file.
This is where your bot token will be loaded from, as well as your database URI (if you're using a database), and most of
your other settings.

It is recommended to import sample_config and extend the Config class, as this will ensure your config contains all
defaults set in the sample_config, hence making it easier to upgrade.

An example `config.env` file could be:

```python
    API_KEY = "" # your bot Token from BotFather
    OWNER_ID = "1234567"  # If you dont know, run the bot and do /id in your private chat with it
    OWNER_USERNAME = "userbotindo" # your telegram username
    SQLALCHEMY_DATABASE_URI = "sqldbtype://username:pw@hostname:port/db_name"
    MONGO_DB_URI = "mongodb+srv://username:pwd@host.port.mongodb.net/db_name"
    MESSAGE_DUMP = "-100987654"  # needed to make sure 'save from' messages persist
    LOAD = "" # list of loaded modules (seperate with space)
    NO_LOAD = "afk android" # list of unloaded modules (seperate with space)
    STRICT_GBAN = True
```

### Python dependencies

Install the necessary Python dependencies by moving to the project directory and running:

`pip3 install -r requirements.txt`.

This will install all the necessary python packages.

### Database

#### MongoDB

[MongoDB](https://cloud.mongodb.com/) here is used to store users, chats, afk status, blacklist, global bans, data.

#### SQL

If you wish to use a database-dependent module (eg: locks, notes, filters, welcomes),
you'll need to have a database installed on your system. I use Postgres, so I recommend using it for optimal compatibility.

In the case of Postgres, this is how you would set up a database on a Debian/Ubuntu system. Other distributions may vary.

- install PostgreSQL:

`sudo apt-get update && sudo apt-get install postgresql`

- change to the Postgres user:

`sudo su - postgres`

- create a new database user (change YOUR_USER appropriately):

`createuser -P -s -e YOUR_USER`

This will be followed by you need to input your password.

- create a new database table:

`createdb -O YOUR_USER YOUR_DB_NAME`

Change YOUR_USER and YOUR_DB_NAME appropriately.

- finally:

`psql YOUR_DB_NAME -h YOUR_HOST YOUR_USER`

This will allow you to connect to your database via your terminal.
By default, YOUR_HOST should be 0.0.0.0:5432.

You should now be able to build your database URI. This will be:

`sqldbtype://username:pw@hostname:port/db_name`

Replace SqlDbType with whichever DB you're using (eg Postgres, MySQL, SQLite, etc)
repeat for your username, password, hostname (localhost?), port (5432?), and DB name.

## Modules

### Setting load order

The module load order can be changed via the `LOAD` and `NO_LOAD` configuration settings.
These should both represent lists.

If `LOAD` is an empty list, all modules in `modules/` will be selected for loading by default.

If `NO_LOAD` is not present or is an empty list, all modules selected for loading will be loaded.

If a module is in both `LOAD` and `NO_LOAD`, the module will not be loaded - `NO_LOAD` takes priority.

### Creating your own modules

Creating a module has been simplified as much as possible - but do not hesitate to suggest further simplification.

All that is needed is that your .py file is in the modules folder.

To add commands, make sure to import the dispatcher via

`from ubotindo import dispatcher`.

You can then add commands using the usual

`dispatcher.add_handler()`.

Assigning the `__help__` variable to a string describing this modules' available
commands will allow the bot to load it and add the documentation for
your module to the `/help` command. Setting the `__mod_name__` variable will also allow you to use a nicer,
user-friendly name for a module.

The `__migrate__()` function is used for migrating chats - when a chat is upgraded to a supergroup, the ID changes, so
it is necessary to migrate it in the DB.

The `__stats__()` function is for retrieving module statistics, eg number of users, number of chats. This is accessed
through the `/stats` command, which is only available to the bot owner.
