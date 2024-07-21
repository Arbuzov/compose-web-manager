"""
This module works as proxy connector
to support the outdated libs
"""

import logging

__all__ = ("all_tasks", "current_task")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:

    from asyncio import all_tasks, current_task

except ImportError as error:
    logger.error("Import error %s", error)
    from asyncio import Task

    all_tasks = Task.all_tasks
    current_task = Task.current_task
