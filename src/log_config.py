import logging
import logging.config
import traceback

logging.config.fileConfig('logging.conf')

def get_logger(name):
    # create logger
    return logging.getLogger(name)

# # 'application' code
# logger.debug('debug message')
# logger.info('info message')
# logger.warning('warn message')
# logger.error('error message')
# logger.critical('critical message')
