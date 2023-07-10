import sys
import logging
from loguru import logger
from bot import config

LEVEL = logging.DEBUG if config.DEBUG else logging.INFO


class InterceptHandler(logging.Handler):
    LEVELS_MAP = {
        logging.CRITICAL: "CRITICAL",
        logging.ERROR: "ERROR",
        logging.WARNING: "WARNING",
        logging.INFO: "INFO",
        logging.DEBUG: "DEBUG",
    }

    def _get_level(self, record):
        return self.LEVELS_MAP.get(record.levelno, record.levelno)

    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(self._get_level(record), record.getMessage())


def setup():
    logger.remove(0)
    logger.add(sys.stderr, level=LEVEL)
    logger.add(config.LOG_DIR / "log.log", rotation="49 MB", compression='zip', encoding="utf8")
    logging.basicConfig(handlers=[InterceptHandler()], level=LEVEL)
    # logger.disable("apscheduler")
    # logger.enable("db_client")
    # logger.enable("tortoise")
    # logger.disable('aiogram')
    # logger.disable("sqlalchemy.engine.base")
    # logger.enable('aiogram')