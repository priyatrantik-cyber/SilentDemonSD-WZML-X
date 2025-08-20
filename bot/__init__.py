#!/usr/bin/env python3
from tzlocal import get_localzone
from pytz import timezone
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client as tgClient, enums
from pymongo import MongoClient
from asyncio import Lock
from dotenv import load_dotenv, dotenv_values
from threading import Thread
from time import sleep, time
from subprocess import Popen, run as srun
from os import remove as osremove, path as ospath, environ, getcwd
# from aria2p import API as ariaAPI, Client as ariaClient   # ❌ disabled aria2
# from qbittorrentapi import Client as qbClient             # ❌ disabled qBittorrent
from faulthandler import enable as faulthandler_enable
from socket import setdefaulttimeout
from logging import getLogger, Formatter, FileHandler, StreamHandler, INFO, basicConfig, error as log_error, info as log_info, warning as log_warning
from uvloop import install

faulthandler_enable()
install()
setdefaulttimeout(600)

botStartTime = time()

basicConfig(format="[%(asctime)s] [%(levelname)s] - %(message)s - ( %(filename)s, %(lineno)d )",
            datefmt="%d-%b-%y %I:%M:%S %p",
            handlers=[FileHandler('log.txt'), StreamHandler()],
            level=INFO)

LOGGER = getLogger(__name__)

load_dotenv('config.env', override=True)

Interval = []
QbInterval = []
QbTorrents = {}
GLOBAL_EXTENSION_FILTER = ['aria2', '!qB']
user_data = {}
extra_buttons = {}
list_drives_dict = {}
shorteners_list = []
categories_dict = {}
gd_search_dict = {}
aria2_options = {}
qbit_options = {}
queued_dl = {}
queued_up = {}
bot_cache = {}
non_queued_dl = set()
non_queued_up = set()

# 🚫 Removed the "README.md file there to be read" blocker
# try:
#     if bool(environ.get('_____REMOVE_THIS_LINE_____')):
#         log_error('The README.md file there to be read! Exiting now!')
#         exit()
# except:
#     pass

download_dict_lock = Lock()
status_reply_dict_lock = Lock()
queue_dict_lock = Lock()
qb_listener_lock = Lock()
status_reply_dict = {}
download_dict = {}
rss_dict = {}

BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    log_error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

bot_id = BOT_TOKEN.split(':', 1)[0]

DATABASE_URL = environ.get('DATABASE_URL', '')
if len(DATABASE_URL) == 0:
    DATABASE_URL = ''

if DATABASE_URL:
    conn = MongoClient(DATABASE_URL)
    db = conn.wzmlx
    current_config = dict(dotenv_values('config.env'))
    old_config = db.settings.deployConfig.find_one({'_id': bot_id})
    if old_config is None:
        db.settings.deployConfig.replace_one(
            {'_id': bot_id}, current_config, upsert=True)
    else:
        del old_config['_id']
    if old_config and old_config != current_config:
        db.settings.deployConfig.replace_one(
            {'_id': bot_id}, current_config, upsert=True)
    elif config_dict := db.settings.config.find_one({'_id': bot_id}):
        del config_dict['_id']
        for key, value in config_dict.items():
            environ[key] = str(value)
    if pf_dict := db.settings.files.find_one({'_id': bot_id}):
        del pf_dict['_id']
        for key, value in pf_dict.items():
            if value:
                file_ = key.replace('__', '.')
                with open(file_, 'wb+') as f:
                    f.write(value)
    if a2c_options := db.settings.aria2c.find_one({'_id': bot_id}):
        del a2c_options['_id']
        aria2_options = a2c_options
    if qbit_opt := db.settings.qbittorrent.find_one({'_id': bot_id}):
        del qbit_opt['_id']
        qbit_options = qbit_opt
    conn.close()
    BOT_TOKEN = environ.get('BOT_TOKEN', '')
    bot_id = BOT_TOKEN.split(':', 1)[0]
    DATABASE_URL = environ.get('DATABASE_URL', '')
else:
    config_dict = {}

# ⚠️ All qBittorrent / aria2 startup disabled:
# srun(["qbittorrent-nox", "-d", f"--profile={getcwd()}"])
# srun(["chmod", "+x", "aria.sh"])
# srun("./aria.sh", shell=True)
# aria2 = ariaAPI(ariaClient(host="http://localhost", port=6800, secret=""))
# def get_client():
#     return qbClient(host="localhost", port=8090, VERIFY_WEBUI_CERTIFICATE=False, REQUESTS_ARGS={'timeout': (30, 60)})

# Thread(target=aria2c_init).start()

log_info("Creating client from BOT_TOKEN")
bot = tgClient('bot', environ.get("TELEGRAM_API"), environ.get("TELEGRAM_HASH"),
               bot_token=BOT_TOKEN, workers=1000,
               parse_mode=enums.ParseMode.HTML).start()
bot_loop = bot.loop
bot_name = bot.me.username
scheduler = AsyncIOScheduler(timezone=str(get_localzone()), event_loop=bot_loop)
