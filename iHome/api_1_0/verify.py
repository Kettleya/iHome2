# -*- coding:utf-8 -*-
# 验证码的提供：图片验证码和短信验证码
import random
import re
from flask import json
from iHome.utils.sms import CCP
from flask import abort
from flask import current_app
from flask import make_response
from flask import request, jsonify
from iHome import constants
from iHome.utils.response_code import RET
from . import api
from iHome import redis_store
from iHome.utils.captcha.captcha import captcha


@api.route('/sms_code', methods=['POST'])
def send_sms_code():
    """
    1. 获取前端通过ajax发来的json数据,并转义成python字典
    2. 获取并校验参数
    3. 从Redis中取出图片验证码(如果找不到,则验证码已经过期)
    4. 进行验证码的对比,如果验证码不一致则return
    5. 校验手机号是否符合规范
    6. 生成短信内容(random生成随机6位验证码)
    7. 发送短信
    8. 保存短信验证到redis中
    9. 告诉前端发送短信成功
    :return:
    """
    # 1.接收前端发来的参数
    # JSON字符串
    json_data = request.data
    # 转成字典
    json_dict = json.loads(json_data)
    mobile = json_dict.get('mobile')
    image_code = json_dict.get('image_code')
    image_code_id = json_dict.get('image_code_id')

    # 2.判断参数是否有值和校验参数
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 3.取出图片验证码
    try:
        real_image_code = redis_store.get('ImageCode:' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询验证码出错')

    # 如果验证码不存在,则说明验证码已经过期
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='验证码已过期')

    # 4.进行验证码的对比,如果不一致则return
    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR,errmsg='验证码输入不正确')

        # 5.校验手机验证码是否符合规范
    if not re.match('^1[34578][0-9]{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式有误')

    # 6.使用random生成6位随机数
    sms_code = "%06d" % random.randint(1, 999999)
    current_app.logger.debug('短信验证码为:' + sms_code)

    # 7. 发送短信
    # result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], "1")
    # if result != 1:
    #     # 发送短信失败
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送短信失败")

    # 8. 保存短信验证到redis中
    try:
        redis_store.set(mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存验证码失败')

    # 9.告知前端短信发送成功
    return jsonify(errno=RET.OK, errmsg='发送成功')


@api.route("/image_code")
def get_image_code():
    """
    图片验证码的视图函数
    1. 取到图片编码
    2. 生成图片验证码
    3. 将图片验证码内容通过图片编码保存到redis中
    4. 返回图片

    :return:
    """

    # 1. 取到图片编码
    cur_id = request.args.get("cur_id")
    pre_id = request.args.get("pre_id")

    if not cur_id:
        abort(403)

    # 2. 生成图片验证码
    _, text, image = captcha.generate_captcha()
    current_app.logger.debug("图片验证码为：" + text)
    # 3. 将图片验证码内容通过图片编码保存到redis中
    try:
        redis_store.set("ImageCode:" + cur_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
        if pre_id:
            redis_store.delete("ImageCode:" + pre_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存验证码数据失败")

    # 返回图片验证码的图片
    response = make_response(image)
    # 设置响应的内容类型
    response.headers["Content-Type"] = "image/jpg"
    # 进行返回
    return response
