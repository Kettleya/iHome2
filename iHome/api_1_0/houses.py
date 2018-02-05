# -*- coding:utf-8 -*-
import datetime
from flask import current_app
from flask import g
from flask import jsonify
from flask import request
from flask import session
from iHome import constants, db
from iHome import redis_store
from iHome.api_1_0 import api
from iHome.models import Area, Facility, House, HouseImage, Order
from iHome.utils import image_storage
from iHome.utils.common import login_required
from iHome.utils.response_code import RET


@api.route('/houses')
def search_houses():
    """
    搜索房屋信息
    :return:
    """
    current_app.logger.debug(request.args)
    aid = request.args.get('aid','')
    sd= request.args.get('sd','')
    ed= request.args.get('ed','')
    sk= request.args.get('sk','new')
    page = request.args.get('p','1')

    start_date =None
    end_date =None

    # 判断参数
    try:
        page = int(page)
        # 转换成时间对象
        if sd:
            start_date = datetime.datetime.strptime(sd,'%Y-%m-%d')
        if ed:
            end_date = datetime.datetime.strptime(ed,'%Y-%m-%d')
        if start_date and end_date:
            assert start_date < end_date, Exception ('结束日期必须大于开始时间')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 从缓存中获取数据
    try:
        redis_name = 'house_list_%s_%s_%s_%s'%(aid,sk,sd,ed)
        #取出缓存的值
        resp = redis_store.hget(redis_name,page)
        if resp:
            return jsonify(errno=RET.OK, errmsg='OK',data=eval(resp))
    except Exception as e:
        current_app.logger.error(e)

    # 查询所有数据
    try:
        house_query = House.query

        # 根据地区筛选
        if aid:
            house_query = house_query.filter(House.area_id == aid)

        # 通过搜索时间去查询冲突的订单
        conflict_orders = []
        if start_date and end_date:
            conflict_orders = Order.query.filter(end_date>Order.begin_date,start_date<Order.end_date).all()

        if conflict_orders:
            # 取到冲突订单里的所有id
            conflict_house_ids = [order.house_id for order in conflict_orders ]
            house_query = house_query.filter(House.id.notin_(conflict_house_ids))

        if sk == 'booking':
            house_query = house_query.order_by(House.order_count.desc())
        elif sk == 'price-inc':
            house_query = house_query.order_by(House.price.asc())
        elif sk == 'price-des':
            house_query = house_query.order_by(House.price.desc())
        else:
            house_query = house_query.order_by(House.create_time.desc())

        # 使用paginate进行分页
        paginate = house_query.paginate(page,constants.HOUSE_LIST_PAGE_CAPACITY,False)
        # 当前页
        houses = paginate.items
        # 总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据失败')

    # 查询出所有房屋信息,并转成字典
    houses_dict = []
    for house in houses:
        houses_dict.append(house.to_basic_dict())

    resp={'total_page':total_page,'houses':houses_dict}

    # 进行redis存储
    try:
        redies_name = 'house_list_%s_%s_%s_%s'%(aid,sk,sd,ed)
        # 获取redis管道对象
        pipeline = redis_store.pipeline()
        # 开启事物
        pipeline.multi()

        # 设置数据
        pipeline.hset(redis_name,page,resp)
        # 设置数据过期时间
        pipeline.expire(redis_name,constants.HOUSE_LIST_REDIS_EXPIRES)

        # 执行,提交事务
        pipeline.execute()
    except Exception as e:
        current_app.logger.error(e)

    # 返回响应
    return jsonify(errno=RET.OK, errmsg='OK',data=resp)

@api.route('/houses/index')
def get_house_index():
    """
    获取首页推荐房屋
    1.获取房屋数据并展示
    2.将房屋列表转成字典类型
    3.进行响应
    :return:
    """
    try:
        houses = House.query.order_by(House.create_time.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
    except Exception as e:
        houses=[]
        current_app.logger.error(e)

    # 将房屋列表转成字典类型
    house_dict_li = []
    for house in houses:
        house_dict_li.append(house.to_basic_dict())

    # 进行响应
    return jsonify(errno=RET.OK, errmsg='OK',data=house_dict_li)


@api.route('/houses/<int:house_id>')
def house_detail(house_id):
    """
    1.通过house_id查询指定房屋类型
    2.将房屋的详情信息封装成字典
    3.返回并给出响应
    :param house_id: 房屋id
    :return:
    """
    # 1.通过house_id查询指定房屋类型
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询房屋信息失败')

    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    # 2.将房屋的详情信息封装成字典
    resp_dict = house.to_full_dict()

    # 取到当前用户的id.如果没有用户登陆,就返回-1
    user_id = session.get('user_id', -1)

    # 3.返回并给出响应
    return jsonify(errno=RET.OK, errmsg='OK', data={'house': resp_dict, 'user_id': user_id})


@api.route('/houses/image', methods=['POST'])
@login_required
def upload_house_image():
    """
    1.取到参数,图片,房屋id
    2.取到指定房屋id模型
    3.上传图片到七牛云
    4.初始化房屋图片的模型
    5.设置数据并保存到数据库
    6.返回响应-->图片的url
    :return:
    """
    # 1.取到参数,图片,房屋id
    try:
        house_image = request.files.get('house_image').read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 取到房屋id
    house_id = request.form.get('house_id')

    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 2.取到指定房屋id模型
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询房屋数据失败')

    if not house:
        return jsonify(errno=RET.NODATA, errmsg='当前房屋不存在')

    # 3.上传图片到七牛云
    try:
        key = image_storage.upload_image(house_image)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')

    # 判断当前房屋是否设置了index_image,如果没有设置就设置
    if not house.index_image_url:
        house.index_image_url = key

    # 4.初始化房屋图片的模型
    house_image_model = HouseImage()

    # 5.设置数据并且保存到数据库
    house_image_model.house_id = house_id
    house_image_model.url = key

    try:
        db.session.add(house_image_model)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='添加图片数据失败')

    # 6.返回响应-->图片的url
    return jsonify(errno=RET.OK, errmsg='上传成功', data={'image_url': constants.QINIU_DOMIN_PREFIX + key})


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
