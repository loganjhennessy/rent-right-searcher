"""rentright.utils.log"""
import logging

LEVEL = "INFO"
loggers = {}

def get_configured_logger(name):

    if loggers.get(name):
        return loggers.get(name)

    else:
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, LEVEL))

        if not logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(getattr(logging, LEVEL))

            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            formatter = logging.Formatter(format_string)

            ch.setFormatter(formatter)

            logger.addHandler(ch)

        loggers.update(dict(name=logger))

        return logger
