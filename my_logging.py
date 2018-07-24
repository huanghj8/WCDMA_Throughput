import logging

import time


class MyLogging(object):
    def __init__(self):
        self.local_time = time.strftime("%Y%m%d-%H%M%S")

    def get_logger(self):
        logger = logging.getLogger("Logger")
        logger.setLevel(logging.DEBUG)
        self.file_handler = logging.FileHandler('result\Testlog_%s.log' % self.local_time)
        self.file_handler.setLevel(logging.DEBUG)
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter(
            '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        self.file_handler.setFormatter(self.formatter)
        self.console_handler.setFormatter(self.formatter)
        logger.addHandler(self.file_handler)
        logger.addHandler(self.console_handler)
        return logger
