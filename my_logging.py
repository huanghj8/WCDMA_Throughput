import logging
import time
import os
# import ctypes

import sys
from rainbow_logging_handler import RainbowLoggingHandler

# FOREGROUND_WHITE = 0x0007
# FOREGROUND_BLUE = 0x01  # text color contains blue.
# FOREGROUND_GREEN = 0x02  # text color contains green.
# FOREGROUND_RED = 0x04  # text color contains red.
# FOREGROUND_YELLOW = FOREGROUND_RED | FOREGROUND_GREEN
# STD_OUTPUT_HANDLE = -11
# std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)


class MyLogging(object):
    def __init__(self):
        self.formatter = logging.Formatter(
            '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        # setup RainbowLoggingHandler
        self.local_time = time.strftime("%Y%m%d-%H%M%S")
        # abandon cosole handler
        # self.console_handler = logging.StreamHandler()
        self.path = 'result\log\Testlog_%s.log' % self.local_time
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.file_handler = logging.FileHandler(self.path)
        self.color_handler = RainbowLoggingHandler(sys.stderr, color_funcName=('black', 'yellow', True))

    def get_logger(self):
        logger = logging.getLogger("Logger")
        logger.setLevel(logging.DEBUG)
        self.file_handler.setLevel(logging.DEBUG)
        # self.console_handler.setLevel(logging.DEBUG)
        # self.console_handler.setFormatter(self.formatter)
        self.file_handler.setFormatter(self.formatter)
        self.color_handler.setFormatter(self.formatter)
        logger.addHandler(self.file_handler)
        # logger.addHandler(self.console_handler)
        logger.addHandler(self.color_handler)
        return logger

    # def set_color(self, color, handle=std_out_handle):
    #     bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
    #     return bool
    #
    # def error(self, mess, color=FOREGROUND_RED):
    #     self.set_color(color)
    #     logger = self.get_logger()
    #     logger.error(mess)
    #     self.set_color(FOREGROUND_WHITE)
