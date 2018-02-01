# -*- coding:utf-8 -*-
import functools
from flask import g
from flask import session, jsonify
from werkzeug.routing import BaseConverter
from iHome.utils.response_code import RET


class RegexConverter(BaseConverter):
    """定义正则路由的转换器"""

    def __init__(self, url_map, *args):
        super(RegexConverter, self).__init__(url_map)
        self.regex = args[0]

def login_required(func):

    # 防止不同函数调用时,函数名不被修改
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        # if用户没有登陆:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
        else:
            # 使用g变量去存储用户的id,再执行具体的视图函数时就可以不用再次去视图函数中取session
            g.user_id = user_id
            return func(*args,**kwargs)
    return wrapper