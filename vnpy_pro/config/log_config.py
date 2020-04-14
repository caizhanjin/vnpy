import logging.config
import os


def initialize_logging(log_base_path):
    if not os.path.isdir(log_base_path):
        os.mkdir(log_base_path)

    LOD_DICT_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,  # 是否禁用已经存在的日志器
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'simple': {  # 日志记录级别+时间日期+模块名称+函数名称+行号+记录消息
                'format': '%(levelname)s %(asctime)s %(module)s %(funcName)s %(lineno)d %(message)s'
            },
        },
        'filters': {},
        'handlers': {
            'default': {  # 打印到终端的日志
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
            'access': {  # 保存到文件，收集info及以上的日志
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'simple',
                'filename': os.path.join(log_base_path, 'main.log'),
                'maxBytes': 1024 * 1024 * 5,  # 5M
                'backupCount': 5,
                'encoding': 'utf-8',
            },
            'severe': {  # 保存到文件，收集error及以上的日志
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'simple',
                'filename': os.path.join(log_base_path, 'main.log'),
                'maxBytes': 1024*1024*5,
                'backupCount': 5,
                'encoding': 'utf-8',
            },
            'test_handler': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'simple',
                'filename': os.path.join(log_base_path, 'test.log'),
                'maxBytes': 1024 * 1024 * 5,
                'backupCount': 5,
                'encoding': 'utf-8',
            },
            'db_handler': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'simple',
                'filename': os.path.join(log_base_path, 'db.log'),
                'maxBytes': 1024 * 1024 * 5,
                'backupCount': 5,
                'encoding': 'utf-8',
            },
        },
        'loggers': {
            '': {  # 默认实例，即打印又写入文件 logging.getLogger(__name__)，key为空时
                'handlers': ['default', 'access', 'severe'],
                'level': 'INFO',
                'propagate': True  # 向上（更高level的logger）传递
            },
            'test_logger': {
                'handlers': ['test_handler'],
                'level': 'INFO',
                'propagate': True
            },
            'db_logger': {
                'handlers': ['default', 'db_handler'],
                'level': 'INFO',
                'propagate': True
            },
        }
    }

    logging.config.dictConfig(LOD_DICT_CONFIG)


# logging.getLogger(__name__) 会拿到logger配置
# logging.getLogger(__name__)，不同的文件__name__不同，打印日志时就会标识信息不同，
# key查找不到时，就会使用默认实例（key=""）

# 使用示例1：
# logger = logging.getLogger(__name__)
# logger.info('It works!')

# 使用示例2：
# test_logger = logging.getLogger("test_logger")
# try:
#     open('/path/to/does/not/exist', 'rb')
# except Exception as e:
#     # 使用参数 exc_info=true 调用 logger 方法, traceback 会输出到 logger
#     test_logger.error("Failed to open file", exc_info=True)


