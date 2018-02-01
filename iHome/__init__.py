# -*- coding:utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_session import Session
import redis
from config import config
from iHome.utils.common import RegexConverter

db = SQLAlchemy()

redis_store = None


def setup_logging(level):
    # 设置日志的记录等级
    logging.basicConfig(level=level)  # 调试debug级
    # 创建日志记录器,指明日志的保存路径,每个日志文件的最大大小,保存的日志文件个数上限
    file_log_handler = RotatingFileHandler('logs/log', maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志的记录格式
    formatter = logging.Formatter('%(levelname)%s %(filename)%s:%(lineno)%d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象,添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    # 调用日志函数,并且传入=当前配置的日志等级
    setup_logging(config[config_name].LOGGING_LEVEL)

    app = Flask(__name__)

    app.config.from_object(config[config_name])

    # db = SQLAlchemy(app)
    db.init_app(app)

    global redis_store
    redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT)

    # 开启CSRF保护
    CSRFProtect(app)
    # 指定Session保存的位置
    Session(app)

    app.url_map.converters['re'] = RegexConverter

    # 注册蓝图,再使用时引入
    from iHome.api_1_0 import api
    app.register_blueprint(api, url_prefix='/api/v1.0')

    from web_html import html
    app.register_blueprint(html)

    return app
