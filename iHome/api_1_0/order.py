# -*- coding:utf-8 -*-
import datetime

from flask import current_app
from flask import g
from flask import request, jsonify

from iHome import db
from iHome.api_1_0 import api
from iHome.models import House, Order
from iHome.utils.common import login_required
from iHome.utils.response_code import RET


@api.route('/orders', methods=['POST'])
@login_required
def make_orders():
    """
    1.获取参数并校验,住房id,用户id,开始日期,结束日期
    2.从数据库中查询房屋状态(是否已被预定)
    3.如果未被预定,则创建订单及相关数据
    4.将数据保存到数据库
    5.给出响应
    :return:
    """
    # 1.获取参数并校验
    json_dict = request.json
    start_date_str = json_dict.get('start_date')
    end_date_str = json_dict.get('end_date')
    house_id = json_dict.get('house_id')

    if not all([start_date_str, end_date_str, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数有误')

    # 判断时间参数
    try:
        # 转为时间参数
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        if start_date and end_date:
            assert start_date < end_date, Exception('开始时间必须小于结束时间')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数有误')

    # 查询房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')

    if not house:
        return jsonify(errno=RET.NODATA, errmsg='该房屋不存在')

    # 2.查询当前房屋状态,是否已被预定
    try:
        conflict_order = Order.query.filter(end_date>Order.begin_date,start_date<Order.end_date,house_id==House.id).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')

    if conflict_order:
        return jsonify(errno=RET.DATAERR, errmsg='该房间已被预定')

    # 3.创建订单模型,存储数据
    days = (end_date - start_date).days
    order = Order()
    order.user_id = g.user_id
    order.house_id = house_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.price= house.price
    order.amount = days*house.price

    # 设置房屋订单数量+1
    house.order_count += 1

    # 4.保存数据
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存订单失败')

    # ５．给出响应
    return jsonify(errno=RET.OK, errmsg='OK')