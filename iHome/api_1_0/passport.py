# -*- coding:utf-8 -*-
import re
from flask import current_app, jsonify
from flask import request
from flask import session
from iHome import redis_store, db
from iHome.models import User
from iHome.utils.response_code import RET
from . import api


@api.route('/session')
def check_login():
    """判断用户是否登陆,如果登陆则显示user_id和name"""
    user_id = session.get('user_id')
    name = session.get('name')
    return jsonify(errno=RET.OK, errmsg='OK', data={'user_id': user_id, 'name': name})


@api.route('/session', methods=['DELETE'])
def logout():
    """执行退出操作"""
    session.pop('name')
    session.pop('user_id')
    session.pop('mobile')

    return jsonify(errno=RET.OK, errmsg='OK')


@api.route('/session', methods=['POST'])
def login():
    """
    1.获取参数并校验
    2.判断手机号是否符合规范
    3.从数据库中获取用户信息
    4.校验密码是否相等
    5.把当前用户信息存入到session中
    6.返回并给出响应
    :return:
    """

    # 1.获取参数并校验,2.判断手机号是否符合规范
    data_dict = request.json
    mobile = data_dict.get('mobile')
    password = data_dict.get('password')

    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数有误')

    if not re.match('^1[34578][0-9]{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式有误')

    # 3.从数据库中获取用户信息
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询失败')

    if not user:
        return jsonify(errno=RET.USERERR, errmsg='用户不存在')

    # 4.校验密码是否相等
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg='密码错误')

    # 5.把当前用户信息存入到session中
    try:
        session['user_id'] = user.id
        session['name'] = user.name
        session['mobile'] = user.mobile
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='用户登陆失败')

    # 6.返回并给出响应
    return jsonify(errno=RET.OK, errmsg='登陆成功')


@api.route('/users', methods=['POST'])
def register():
    """
    1.获取json参数,并转换为python字典,并校验参数
    2.取到真实的短信验证码
    3.对比短信验证码是否与真实验证码匹配
    4.初始化user,保存相关数据
    5.将数据存储到数据库
    6.给出响应
    :return:
    """
    # 1.获取json参数
    data_dict = request.json
    mobile = data_dict.get('mobile')
    phonecode = data_dict.get('phonecode')
    password = data_dict.get('password')

    if not all([mobile, phonecode, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 2.取到真实的短信验证码
    try:
        real_phonecode = redis_store.get(mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询短信验证码失败')

    if not real_phonecode:
        return jsonify(errno=RET.NODATA, errmsg='短信验证码已经过期')

    # 3.进行短信验证码的对比
    if real_phonecode != phonecode:
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码输入错误')

    # 4.初始化User,保存相关数据
    user = User()
    user.mobile = mobile
    user.name = mobile
    # 保存密码
    user.password = password

    # 5.将数据存入数据库中
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存用户数据失败')

    # 6.给出响应
    return jsonify(errno=RET.OK, errmsg='注册成功')
