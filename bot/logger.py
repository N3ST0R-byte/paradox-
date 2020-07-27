import sys
import logging


# Setup the logger
logger = logging.getLogger()
log_fmt = logging.Formatter(fmt='[{asctime}][{levelname:^8}] {message}', datefmt='%d/%m | %H:%M:%S', style='{')
term_handler = logging.StreamHandler(sys.stdout)
term_handler.setFormatter(log_fmt)
logger.addHandler(term_handler)
logger.setLevel(logging.INFO)


def log(message, context="Global".center(22, '='), level=logging.INFO):
    for line in message.split('\n'):
        logger.log(level, '[{}] {}'.format(str(context).center(22, '='), line))
