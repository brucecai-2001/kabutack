import logging
from logging.handlers import TimedRotatingFileHandler


class Logger:
    def __init__(self, log_filename='logs/app.log'):
        # 创建一个logger
        self.logger = logging.getLogger(log_filename)
        self.logger.setLevel(logging.DEBUG)

        # 创建一个处理器，设置为每天生成新的日志文件
        handler = TimedRotatingFileHandler(log_filename, when='midnight', interval=1, backupCount=7)
        handler.setLevel(logging.DEBUG)
        handler.suffix = "%Y-%m-%d"  # 设置日志文件后缀为日期

        # 创建一个格式器并将其添加到处理器中
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)

        # 将处理器添加到logger中
        self.logger.addHandler(handler)

    def log(self, msg_type, msg):
        if msg_type == "User":
            self.logger.info("User says: " + msg)

        elif msg_type == "Assistant":
            self.logger.info("Assistant says: " + msg)
        
        elif msg_type == "Error":
            self.logger.error("Error: " + msg)


# Singleton
logger = Logger()