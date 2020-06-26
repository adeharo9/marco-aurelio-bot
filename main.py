#!/usr/bin/env

import dotenvpy as env
from marcoaurelio import MarcoAurelio


env.load_dotenv()
bot = MarcoAurelio()

if __name__ == '__main__':

    bot.run(env.DISCORD_TOKEN)
