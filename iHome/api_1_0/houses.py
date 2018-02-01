# -*- coding:utf-8 -*-
from flask import current_app
from flask import g
from flask import jsonify
from flask import request
from iHome import constants, db
from iHome import redis_store
from iHome.api_1_0 import api
from iHome.models import Area, Facility, House
from iHome.utils.common import login_required
from iHome.utils.response_code import RET


@api.route('/houses', methods=["POST"])
@login_required
def add_house():
    """
    添加新房屋
    1. 接收所有参数
    2. 判断参数是否有值&参数是否符合规范
    3. 初始化房屋模型，并设置数据
    4. 保存到数据库
    5. 返回响应
    :return:
    """

    # 1. 接收所有参数
    data_dict = request.json
    title = data_dict.get('title')
    price = data_dict.get('price')
    address = data_dict.get('address')
    area_id = data_dict.get('area_id')
    room_count = data_dict.get('room_count')
    acreage = data_dict.get('acreage')
    unit = data_dict.get('unit')
    capacity = data_dict.get('capacity')
    beds = data_dict.get('beds')
    deposit = data_dict.get('deposit')
    min_days = data_dict.get('min_days')
    max_days = data_dict.get('max_days')

    # 2. 判断参数是否有值&参数是否符合规范
    if not all(
            [title, price, address, area_id, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 以分的形式进行保存
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 初始化房屋模型，并设置数据
    house = House()
    house.user_id = g.user_id
    house.area_id = area_id
    house.title = title
    house.price = price
    house.address = address
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days

    # 取到当前房屋的设置列表
    facilities = data_dict.get("facility")
    # [1, 3, 4, 6]

    # 当前房屋对应的所有设置
    house.facilities = Facility.query.filter(Facility.id.in_(facilities)).all()

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="添加数据失败")

    return jsonify(errno=RET.OK, errmsg="OK", data={"house_id": house.id})


@api.route('/areas')
def get_areas():
    """
    1.获取所有的areas数据
    2.返回响应
    :return:
    """
    # 先从缓存中取数据,如果取到直接返回,如果没有取到,再执行后面的逻辑
    try:
        areas_dict_li = redis_store.get('Areas')
        if areas_dict_li:
            return jsonify(errno=RET.OK, errmsg='OK', data=eval(areas_dict_li))
    except Exception as e:
        current_app.logger.error(e)

    try:
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据失败')

    # 定义空列表,用于保存遍历时所转换的字典
    areas_dict_li = []
    # 转模型字典
    for area in areas:
        areas_dict_li.append(area.to_dict())

    # 缓存数据到redis中
    try:
        redis_store.set('Areas', areas_dict_li, constants.AREA_INFO_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)

    # 返回
    return jsonify(errno=RET.OK, errmsg='OK', data=areas_dict_li)
