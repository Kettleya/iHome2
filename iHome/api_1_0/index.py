# -*- coding:utf-8 -*-
import logging

from flask import current_app

from . import api
from iHome import redis_store


@api.route('/index', methods=["GET", "POST"])
def index():
    # 测试redis，因为是测试代码，暂时注释
    redis_store.set("name", "laowang")
    # 设置 session的保存
    # session["name"] = "xiaohua"
    logging.debug("DEBUG LOG")
    logging.info("INFO LOG")
    logging.warn("WARN LOG")
    logging.error("ERROR LOG")
    logging.fatal("FATAL LOG")

    current_app.logger.debug("DEBUG LOG")
    current_app.logger.info("INFO LOG")
    current_app.logger.warn("WARN LOG")
    current_app.logger.error("ERROR LOG")
    current_app.logger.fatal("FATAL LOG")

    return 'index222'
