# coding=utf-8
import logging
import time
import os
import sys
from rainbow_logging_handler import RainbowLoggingHandler


class MyLogging(object):
    """
    自定义logging类
    """

    def __init__(self):
        """
        初始化类
        """
        self.formatter = logging.Formatter(
            '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        self.local_time = time.strftime("%Y%m%d-%H%M%S")
        self.path = 'result\log'
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        # 日志文件
        self.file_handler = logging.FileHandler('result\log\Testlog_%s.log' % self.local_time)
        # 控制台日志
        self.color_handler = RainbowLoggingHandler(sys.stderr, color_funcName=('black', 'yellow', True))

    def get_logger(self):
        """
        获取日志实例
        :return: None
        """
        logger = logging.getLogger("Logger")
        logger.setLevel(logging.DEBUG)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self.formatter)
        self.color_handler.setFormatter(self.formatter)
        logger.addHandler(self.file_handler)
        logger.addHandler(self.color_handler)
        return logger
