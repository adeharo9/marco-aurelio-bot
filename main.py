#!/usr/bin/env

import env
from marcoaurelio.bot import MarcoAurelio


env.load_dotenv()
bot = MarcoAurelio()

if __name__ == '__main__':

    bot.run(env.DISCORD_TOKEN)
