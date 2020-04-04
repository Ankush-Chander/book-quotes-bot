#!/bin/bash
#
source "${HOME}/.virtualenvs/bookbot_env/bin/activate
cd ${HOME}/side_projects/book-quotes-bot/scripts
python3 bookbot.py --tweet
