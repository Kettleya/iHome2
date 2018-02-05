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


@api.route("/orders", methods=["POST"])
@login_required
def create_order():
    """
    添加新订单
    1. 获取参数：房屋id，开始入住时间，结束入住时间
    2. 判断参数/校验参数
    3. 判断当前房屋在当前时间段内是否已经被预订
    4. 创建订单模型并设置相关数据
    5. 添加到数据库
    6. 返回响应
    :return:
    """

    # 1. 获取参数：房屋id，开始入住时间，结束入住时间
    data_dict = request.json
    house_id = data_dict.get("house_id")
    start_date_str = data_dict.get("start_date")
    end_date_str = data_dict.get("end_date")

    # 2. 判断参数/校验参数

    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断参数
    try:
        # 转成时间对象
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        if start_date and end_date:
            assert start_date < end_date, Exception("结束日期必须大于开始时间")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 判断房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="未查询到房屋数据")

    # 3. 判断当前房屋在当前时间段内是否已经被预订
    try:
        conflict_orders = Order.query.filter(end_date > Order.begin_date, start_date < Order.end_date,
                                             Order.house_id == house_id).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据错误")

    if conflict_orders:
        return jsonify(errno=RET.DATAERR, errmsg="当前房屋已被预订")

    # 4. 创建订单模型并设置相关数据
    days = (end_date - start_date).days
    order = Order()
    order.user_id = g.user_id
    order.house_id = house_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.house_price = house.price
    order.amount = days * house.price

    # 设置房屋的订单数量加1
    house.order_count += 1

    # 5. 添加到数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存订单失败")

    # 6. 返回响应
    return jsonify(errno=RET.OK, errmsg="OK")
