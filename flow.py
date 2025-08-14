import asyncio
from logging.handlers import RotatingFileHandler
import random
from time import time
from prefect import flow, get_run_logger
import os
import aiohttp

# run_deployment(name="my-first-flow/my-first-deployment")
os.environ["PREFECT_DISABLE_TELEMETRY"] = "1"  # disable telemetry

import random
import string


import logging
from prefect import flow, get_run_logger

file_log = logging.Logger(name="file")
file_log.handlers = [RotatingFileHandler('latency.log', maxBytes=2000)]

def random_string(length=8):
    letters = string.ascii_letters  # a-zA-Z
    return "".join(random.choice(letters) for _ in range(length))




async def fetch_site():
    logger = get_run_logger()
    await asyncio.sleep(10)
    logger.info(f"Response length: ", )


@flow
async def test_flow(task_id: int, username: str, password: str) -> tuple[int, str, str]:
    print(f"Starting task {task_id}")
    await fetch_site()
    return task_id, username, password

