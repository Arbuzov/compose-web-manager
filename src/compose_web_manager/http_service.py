"""This module contains http server class"""

import logging
import os

import aiohttp_cors
from aiohttp import web
from aiohttp_swagger import setup_swagger

from .routes import routes
from .config import Config

config = Config()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class HttpService:
    """
    ---
    Creates http server. Process unconditional redirects to the secure
    server
    """

    def __init__(self):
        self.app = web.Application(client_max_size=1200 * 1024**2)
        self.runner = None
        self.api_base_url = '/'
        self.swagger_url = '/api/docs'

        for route in routes:
            self.app.router.add_route(route[0], route[1], route[2])
        try:
            api_config = config.path.swagger
            if not os.path.isfile(api_config):
                api_config = "../config/swagger.v1.yaml"
                logger.info(f"API description file: {api_config}")
            setup_swagger(
                self.app,
                api_version="1.0.0",
                swagger_url=self.swagger_url,
                api_base_url=self.api_base_url,
                swagger_from_file=api_config,
            )
        except FileNotFoundError:
            logger.warning("OpenAPI description not found")

        cors = aiohttp_cors.setup(
            self.app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers=[
                        "X-Frontend-Version",
                        "X-Server-Date",
                        "Retry-After",
                    ],
                    allow_headers="*",
                    allow_methods="*",
                    max_age=3600,
                )
            },
        )

        for route in list(self.app.router.routes()):
            if not isinstance(route.resource, web.StaticResource):
                cors.add(route)

    async def start(self):
        """
        ---
        Starts http service
        """
        logger.info("internal web server enabled")
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "0.0.0.0", 8880)
        logger.info("worker started")
        await site.start()

    async def stop(self):
        """
        ---
        Stops http service
        """
        await self.runner.cleanup()
