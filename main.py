# main.py

import asyncio
import logging

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from bot import bot, dp
import bot.handlers # noqa: This import ensures that the handlers are registered
from settings import ENVIRONMENT, SENTRY_DSN

# Initialize Sentry
def init_sentry():
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        integrations=[
            AioHttpIntegration(),
            LoggingIntegration()
        ]
    )

async def main():
    try:
        logging.info('Started')
        await dp.start_polling()
    finally:
        logging.info('Exited')
        await bot.close()

if __name__ == '__main__':
    init_sentry()
    asyncio.run(main())