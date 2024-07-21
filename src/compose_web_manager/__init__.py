"""
Root module for the sbc web manager

@author: Arbuzov Sergey <info@whitediver.com>
"""

import asyncio
import logging
import signal
import sys

from .http_service import HttpService
from .proxy_connector import all_tasks, current_task

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

http = HttpService()

__all__ = ["main"]


async def kill_loop(loop):
    """Watches tasks and stops the loop then all tasks are done"""
    while len([t for t in all_tasks() if t is not current_task()]) > 0:
        await asyncio.sleep(1)
    logger.info("stopping the main loop")
    loop.stop()


def shutdown_handler(loop):
    """'Graceful shutdown"""
    logger.info("shutdown server")
    loop.create_task(http.stop())
    loop.create_task(kill_loop(loop))


def kill():
    """Kills default event loop"""
    loop = asyncio.get_event_loop()
    shutdown_handler(loop)


def main():
    """Main method entry point of the project"""
    loop = asyncio.get_event_loop()

    try:
        signals = [signal.SIGTERM, signal.SIGINT, signal.SIGHUP]
        for _signal in signals:
            loop.add_signal_handler(_signal, shutdown_handler, loop)

    except AttributeError:
        logger.error("signals not implemented completely")
    except NotImplementedError:
        logger.error("signals not implemented")
    try:
        loop.create_task(http.start())
        loop.run_forever()
    except RuntimeError as exception:
        logger.error("runtimeError: %s", exception)
        sys.exit(1)


if __name__ == "__main__":
    main()
