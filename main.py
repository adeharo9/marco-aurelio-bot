#!/usr/bin/env

import os
from marcoaurelio.bot import MarcoAurelio

from dotenv import load_dotenv

load_dotenv()

bot = MarcoAurelio(channel=os.getenv('BOT_CHANNEL'))

if __name__ == '__main__':

    bot.run(os.getenv('DISCORD_TOKEN'))
