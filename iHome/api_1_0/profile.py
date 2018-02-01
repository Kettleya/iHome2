# -*- coding:utf-8 -*-
from flask import current_app, jsonify
from flask import g
from flask import request
from flask import session

from iHome import constants
from iHome import db
from iHome.api_1_0 import api
from iHome.models import User
from iHome.utils.common import login_required
from iHome.utils.image_storage import upload_image
from iHome.utils.response_code import RET


@api.route('/user/auth')
@login_required
def get_user_auth():
    """
    获取用户的实名认证信息
    :return:
    """
    # 1. 查询出当前用户的模型
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    # 2. 封装响应

    resp = {
        "real_name": user.real_name,
        "id_card": user.id_card
    }
    return jsonify(errno=RET.OK, errmsg="OK", data=resp)


@api.route('/user/auth', methods=["POST"])
@login_required
def set_user_auth():
    """
    设置用户实名认证信息
    1. 获取参数，并判断参数是有值
    2. 查询出当前用户的模型
    3. 更新模型
    4. 保存到数据库
    5. 返回响应
    :return:
    """
    pass

    # 1. 获取参数，并判断参数是有值
    data_dict = request.json
    real_name = data_dict.get("real_name")
    id_card = data_dict.get("id_card")

    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 2. 查询出当前用户的模型
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    # 3. 更新模型
    user.real_name = real_name
    user.id_card = id_card

    # 4. 保存到数据库

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

    # 5. 返回响应
    return jsonify(errno=RET.OK, errmsg="保存成功")


@api.route('/user/name', methods=["POST"])
@login_required
def set_user_name():
    """
    修改用户名
    0. 判断用户是否登录
    1. 获取传过来的用户名，并判断是否有值
    2. 查询到当前登录用户
    3. 更新当前登录用户的模型
    4. 并保存到数据库
    5. 返回响应
    :return:
    """

    # 1. 获取传过来的用户名，并判断是否有值
    user_name = request.json.get("name")
    if not user_name:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 2. 查询到当前登录用户
    # user_id = session.get("user_id")
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据出错")

    if not user:
        return jsonify(errno=RET.NODATA, errmsg="当前用户不存在")

    # 3. 更新当前登录用户的模型
    user.name = user_name

    # 4. 并保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    # 更新session中保存的用户名
    session["name"] = user.name
    # 5. 返回响应
    return jsonify(errno=RET.OK, errmsg="保存成功")


@api.route('/user/avatar', methods=['POST'])
@login_required
def upload_avatar():
    """
    0.判断用户是否登陆
    1.获取到上传的图片文件
    2.判断文件是否存在
    3.将文件上传到七牛云
    4.上传成功之后,将图片保存到用户表头像字段
    5.返回响应
    :return:
    """
    # 1.获取到上传的图片文件/2.判断文件是否存在
    try:
        avatar_data = request.files.get('avatar').read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='读取文件失败')

    # 3.上传文件图片到七牛云
    try:
        key = upload_image(avatar_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='图片上传失败')

    # 4.上传成功之后,将图片保存到用户表头像字段
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据失败')

    if not user:
        return jsonify(errno=RET.NODATA, errmsg='用户不存在')

    # 设置值到user的字段上
    user.avatar_url = key

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    # 5.返回响应
    avatar_url = constants.QINIU_DOMIN_PREFIX + key
    return jsonify(errno=RET.OK, errmsg='OK', data={'avatar_url': avatar_url})


@api.route('/user')
@login_required
def get_user_info():
    """
    1.取到当前用户的id
    2.查询指定的用户信息
    3.组织数据,进行返回
    :return:
    """

    # 1.取到当前用户的id
    user_id = g.user_id

    # 2.查询指定的用户信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据失败')

    if not user:
        return jsonify(errno=RET.NODATA, errmsg='用户不存在')

    # 3.组织数据,进行返回
    return jsonify(errno=RET.OK, errmsg='OK', data=user.to_dict())
