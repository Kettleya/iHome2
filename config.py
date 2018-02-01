# -*- coding:utf-8 -*-
import logging
import redis


class Config(object):
    SECRET_KEY = 'AUaVw+g8OahIv1DDItHbRAfdeTtlItQldxvIhdovdcTCKlh/fGfhxb+CXYTJHSJC'
    """设置配置"""
    DEBUG = True
    # 数据库的配置信息
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/ihome'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis的配置
    REDIS_HOST = '192.168.80.128'  # 上传时记得修改成服务器的127.0.0.1
    REDIS_PORT = 6379

    # 设置session保存参数
    SESSION_TYPE = 'redis'
    # 设置和保存session的相关配置信息
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 开启session签名
    SESSION_USER_SIGNER = True
    # 设置Session生命周期
    PERMANENT_SESSION_LIFETIME = 172800
    # 开发环境日志等级
    LOGGING_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """开发环境的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境下的配置"""
    # 数据库的配置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/ihome2'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
