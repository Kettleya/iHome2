# -*- coding:utf-8 -*-
from flask import current_app, jsonify
from flask import g
from flask import request

from iHome import constants
from iHome import db
from iHome.api_1_0 import api
from iHome.models import User
from iHome.utils.common import login_required
from iHome.utils.image_storage import upload_image
from iHome.utils.response_code import RET


@api.route('/user/avatar',methods=['POST'])
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
    return jsonify(errno=RET.OK, errmsg='OK',data={'avatar_url':avatar_url})


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
    return jsonify(errno=RET.OK, errmsg='OK',data=user.to_dict())